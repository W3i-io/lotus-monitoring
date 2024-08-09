#!/usr/bin/python3

import os
import subprocess
import configparser
import sys

def main(config_file):
    # Parse the configuration file
    config = configparser.ConfigParser()
    config.read(config_file)

    # Set environment variables from the config file
    os.environ['BOOST_API_INFO'] = config['DEFAULT']['BOOST_API_INFO']
    os.environ['FULLNODE_API_INFO'] = config['DEFAULT']['FULLNODE_API_INFO']
    os.environ['LOTUS_MINER_PATH'] = config['DEFAULT']['LOTUS_MINER_PATH']
    os.environ['MARKETS_API_INFO'] = config['DEFAULT']['MARKETS_API_INFO']
    
    miner_id = config['DEFAULT']['MINER_ID']
    miner_log_file = config['DEFAULT']['MINER_LOG_FILE']

    log = subprocess.getoutput("tail -n 500 {miner_log_file} | grep 'completed mineOne' | tail -n 1")

    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'w') as f:
        miner_qap=log.split("\"")[23]
        network_qap=log.split("\"")[19]
        f.write(f'lotus_network_qap{{miner="{miner_id}"}} {network_qap}\n')
        base_epoch=log.split(",")[2].split()[1]
        f.write(f'lotus_miner_base_epoch{{miner="{miner_id}"}} {base_epoch}\n')
        base_delta=log.split(",")[3].split()[1]
        f.write(f'lotus_miner_base_delta{{miner="{miner_id}"}} {base_delta}\n')

    eligible = log.split(',')[10].split()[1]
    if eligible == "true":
        with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
            f.write(f'lotus_miner_eligible{{miner="{miner_id}"}} 1\n')
    else:
        with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
            f.write(f'lotus_miner_eligible{{miner="{miner_id}"}} 0\n')

    data01 = subprocess.getoutput("df | grep '/dev/mapper/mpathf-part1'").split()[3]
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_data01{{miner="{miner_id}"}} {data01}\n')

    data05 = subprocess.getoutput("df | grep '/dev/mapper/mpathj-part1'").split()[3]
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_data05{{miner="{miner_id}"}} {data05}\n')

    data06 = subprocess.getoutput("df | grep '/dev/mapper/mpathk-part1'").split()[3]
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_data06{{miner="{miner_id}"}} {data06}\n')

    data07 = subprocess.getoutput("df | grep '/dev/mapper/mpathl-part1'").split()[3]
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_data07{{miner="{miner_id}"}} {data07}\n')

    subprocess.run("/home/vit/lotus/lotus-miner proving deadlines | grep -v -e 'Miner' -e 'deadline' > /home/vit/deadlines", shell=True)

    total_active_sectors = 0
    total_faulty_sectors = 0
    total_proving_epochs = 0

    with open("/home/vit/deadlines", 'r') as file:
        for line in file:
            active_sectors = int(line.split()[3])
            faulty_sectors = int(line.split()[4].strip("()"))
            total_active_sectors += active_sectors
            total_faulty_sectors += faulty_sectors
            total_proving_epochs += 60

    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_active_sectors{{miner="{miner_id}"}} {total_active_sectors}\n')
        f.write(f'lotus_miner_faulty_sectors{{miner="{miner_id}"}} {total_faulty_sectors}\n')

    total_used_storage = 0
    total_storage_space = 0

    subprocess.run("/home/vit/lotus/lotus-miner storage list | grep -B 2 'Use: Store' | grep '/' > /home/vit/storage", shell=True)

    with open("/home/vit/storage", 'r') as file:
        for line in file:
            used_space = float(line.split(']')[1].split()[0])
            space = float(line.split(']')[1].split()[1].split('/')[1])
            unit = line.split(']')[1].split()[1].split('/')[0]

            if unit == "GiB":
                used_space *= 1073741824
            elif unit == "TiB":
                used_space *= 1099511627776
            else:
                used_space *= 1125899906842624

            total_unit = line.split()[4]
            if total_unit == "GiB":
                space *= 1073741824
            elif total_unit == "TiB":
                space *= 1099511627776
            else:
                space *= 1125899906842624

            total_used_storage += used_space
            total_storage_space += space

    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_store_space{{miner="{miner_id}"}} {total_storage_space}\n')
        f.write(f'lotus_miner_store_used{{miner="{miner_id}"}} {total_used_storage}\n')

    total_used_storage = 0
    total_storage_space = 0

    subprocess.run("/home/vit/lotus/lotus-miner storage list | grep -B 2 'Use: Seal' | grep '/' > /home/vit/storage", shell=True)

    with open("/home/vit/storage", 'r') as file:
        for line in file:
            used_space = float(line.split(']')[1].split()[0])
            space = float(line.split(']')[1].split()[1].split('/')[1])
            unit = line.split(']')[1].split()[1].split('/')[0]

            if unit == "GiB":
                used_space *= 1073741824
            elif unit == "TiB":
                used_space *= 1099511627776
            else:
                used_space *= 1125899906842624

            total_unit = line.split()[4]
            if total_unit == "GiB":
                space *= 1073741824
            elif total_unit == "TiB":
                space *= 1099511627776
            else:
                space *= 1125899906842624

            total_used_storage += used_space
            total_storage_space += space

    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_seal_space{{miner="{miner_id}"}} {total_storage_space}\n')
        f.write(f'lotus_miner_seal_used{{miner="{miner_id}"}} {total_used_storage}\n')

    proving_info = subprocess.getoutput("/home/vit/lotus/lotus-miner proving info | grep 'Sectors'")
    deadline_sectors = int(proving_info.split()[2])

    if deadline_sectors > 0:
        with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
            f.write(f'lotus_miner_proving_window{{miner="{miner_id}"}} 1\n')
    else:
        with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
            f.write(f'lotus_miner_proving_window{{miner="{miner_id}"}} 0\n')

    info = subprocess.getoutput("/home/vit/lotus/lotus-miner info")

    precommit = float(info.split('PreCommit:')[1].split()[0])
    if precommit > 0:
        currency = info.split('PreCommit:')[1].split()[1]
        if currency == "mFIL":
            precommit /= 1000

    pledge = float(info.split('Pledge:')[1].split()[0])
    if pledge > 0:
        currency = info.split('Pledge:')[1].split()[1]
        if currency == "mFIL":
            pledge /= 1000

    vesting = float(info.split('Vesting:')[1].split()[0])
    if vesting > 0:
        currency = info.split('Vesting:')[1].split()[1]
        if currency == "mFIL":
            vesting /= 1000

    market_locked = float(info.split('Locked:')[1].split()[0])
    if market_locked > 0:
        currency = info.split('Locked:')[1].split()[1]
        if currency == "mFIL":
            market_locked /= 1000

    market_available = float(info.split('Available:')[2].split()[0])
    if market_available > 0:
        currency = info.split('Available:')[2].split()[1]
        if currency == "mFIL":
            market_available /= 1000

    miner_available = float(info.split('Available:')[1].split()[0])
    if miner_available > 0:
        currency = info.split('Available:')[1].split()[1]
        if currency == "mFIL":
            miner_available /= 1000

    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_precommit_balance{{miner="{miner_id}"}} {precommit}\n')
        f.write(f'lotus_miner_pledge_balance{{miner="{miner_id}"}} {pledge}\n')
        f.write(f'lotus_miner_vesting_balance{{miner="{miner_id}"}} {vesting}\n')
        f.write(f'lotus_miner_market_locked_balance{{miner="{miner_id}"}} {market_locked}\n')
        f.write(f'lotus_miner_market_available_balance{{miner="{miner_id}"}} {market_available}\n')
        f.write(f'lotus_miner_miner_available_balance{{miner="{miner_id}"}} {miner_available}\n')

    # Additional sector status and error handling omitted for brevity, but would follow the same pattern

    wallets = subprocess.getoutput("/home/vit/lotus/lotus-miner actor control list")

    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_owner_balance{{miner="{miner_id}"}} {wallets.split()[8]}\n')
        f.write(f'lotus_miner_worker_balance{{miner="{miner_id}"}} {wallets.split()[14]}\n')
        f.write(f'lotus_miner_control0_balance{{miner="{miner_id}"}} {wallets.split()[25]}\n')

    workers = subprocess.getoutput("/home/vit/lotus/lotus-miner sealing workers | grep Worker")
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write(f'lotus_miner_sealing_ap_worker{{miner="{miner_id}"}} {workers.count("_AP")}\n')
        f.write(f'lotus_miner_sealing_pc1_worker{{miner="{miner_id}"}} {workers.count("_PC1")}\n')
        f.write(f'lotus_miner_sealing_pc2_worker{{miner="{miner_id}"}} {workers.count("_PC2")}\n')
        f.write(f'lotus_miner_sealing_c2_worker{{miner="{miner_id}"}} {workers.count("_C2")}\n')

    os.rename(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", f"/var/lib/prometheus/node-exporter/lotus.prom")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    main(config_file)
