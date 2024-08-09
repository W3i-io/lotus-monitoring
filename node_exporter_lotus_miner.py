#!/usr/bin/python3

import os
import subprocess
import configparser
import sys

def load_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config['DEFAULT']

def set_environment_variables(config):
    os.environ['BOOST_API_INFO'] = config['BOOST_API_INFO']
    os.environ['FULLNODE_API_INFO'] = config['FULLNODE_API_INFO']
    os.environ['LOTUS_MINER_PATH'] = config['LOTUS_MINER_PATH']
    os.environ['MARKETS_API_INFO'] = config['MARKETS_API_INFO']

def parse_log_for_metrics(log):
    return {
        "miner_qap": log.split("\"")[23],
        "network_qap": log.split("\"")[19],
        "base_epoch": log.split(",")[2].split()[1],
        "base_delta": log.split(",")[3].split()[1],
        "eligible": log.split(',')[10].split()[1] == "true"
    }

def write_metrics_to_file(path, miner_id, metrics):
    with open(path, 'w') as f:
        f.write(f'lotus_miner_qap{{miner="{miner_id}"}} {metrics["miner_qap"]}\n')
        f.write(f'lotus_network_qap{{miner="{miner_id}"}} {metrics["network_qap"]}\n')
        f.write(f'lotus_miner_base_epoch{{miner="{miner_id}"}} {metrics["base_epoch"]}\n')
        f.write(f'lotus_miner_base_delta{{miner="{miner_id}"}} {metrics["base_delta"]}\n')
        f.write(f'lotus_miner_eligible{{miner="{miner_id}"}} {1 if metrics["eligible"] else 0}\n')

def gather_disk_metrics(disk_paths, disk_labels):
    metrics = {}
    for path, label in zip(disk_paths, disk_labels):
        data = subprocess.getoutput(f"df | grep '{path}'").split()[3]
        metrics[label] = data
    return metrics

def append_disk_metrics_to_file(path, miner_id, disk_metrics):
    with open(path, 'a') as f:
        for label, data in disk_metrics.items():
            f.write(f'lotus_miner_{label}{{miner="{miner_id}"}} {data}\n')

def process_deadlines(file_path):
    total_active_sectors = 0
    total_faulty_sectors = 0

    with open(file_path, 'r') as file:
        for line in file:
            active_sectors = int(line.split()[3])
            faulty_sectors = int(line.split()[4].strip("()"))
            total_active_sectors += active_sectors
            total_faulty_sectors += faulty_sectors

    return total_active_sectors, total_faulty_sectors

def write_deadlines_to_file(path, miner_id, active_sectors, faulty_sectors):
    with open(path, 'a') as f:
        f.write(f'lotus_miner_active_sectors{{miner="{miner_id}"}} {active_sectors}\n')
        f.write(f'lotus_miner_faulty_sectors{{miner="{miner_id}"}} {faulty_sectors}\n')

def currency_divider(value, currency):
    if currency == 'FIL':
        return value
    elif currency == 'mFIL':
        return value/1000
    elif currency == 'nFIL':
        return value/1000000000

    return value

def calculate_storage_metrics(storage_file):
    total_used_storage = 0
    total_storage_space = 0

    with open(storage_file, 'r') as file:
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

    return total_used_storage, total_storage_space

def write_storage_metrics_to_file(path, miner_id, metric_name, used_storage, storage_space):
    with open(path, 'a') as f:
        f.write(f'lotus_miner_{metric_name}_space{{miner="{miner_id}"}} {storage_space}\n')
        f.write(f'lotus_miner_{metric_name}_used{{miner="{miner_id}"}} {used_storage}\n')

def process_proving_window(proving_info):
    deadline_sectors = int(proving_info.split()[2])
    return deadline_sectors > 0

def write_proving_window_to_file(path, miner_id, in_proving_window):
    with open(path, 'a') as f:
        f.write(f'lotus_miner_proving_window{{miner="{miner_id}"}} {1 if in_proving_window else 0}\n')

def gather_balance_metrics(info):
    metrics = {}
    metrics['precommit'] = float(currency_divider(float(info.split('PreCommit:')[1].split()[0]),info.split('PreCommit:')[1].split()[1]))
    metrics['pledge'] = float(currency_divider(float(info.split('Pledge:')[1].split()[0]),info.split('Pledge:')[1].split()[1]))
    metrics['vesting'] = float(currency_divider(float(info.split('Vesting:')[1].split()[0]),info.split('Vesting:')[1].split()[1]))
    metrics['market_locked'] = float(currency_divider(float(info.split('Locked:')[1].split()[0]),info.split('Locked:')[1].split()[1]))
    metrics['market_available'] = float(currency_divider(float(info.split('Available:')[2].split()[0]),info.split('Available:')[2].split()[1]))
    metrics['miner_available'] = float(currency_divider(float(info.split('Available:')[1].split()[0]),info.split('Available:')[1].split()[1]))

    return metrics

def write_balance_metrics_to_file(path, miner_id, metrics):
    with open(path, 'a') as f:
        for key, value in metrics.items():
            f.write(f'lotus_miner_{key}_balance{{miner="{miner_id}"}} {value}\n')

def gather_wallet_balances(wallets):
    return {
        "owner_balance": wallets.split()[8],
        "worker_balance": wallets.split()[14],
        "control0_balance": wallets.split()[25]
    }

def write_wallet_balances_to_file(path, miner_id, wallet_balances):
    with open(path, 'a') as f:
        for label, balance in wallet_balances.items():
            f.write(f'lotus_miner_{label}{{miner="{miner_id}"}} {balance}\n')

def gather_worker_metrics(workers):
    return {
        "ap_worker": workers.count("_AP"),
        "pc1_worker": workers.count("_PC1"),
        "pc2_worker": workers.count("_PC2"),
        "c2_worker": workers.count("_C2")
    }

def write_worker_metrics_to_file(path, miner_id, worker_metrics):
    with open(path, 'a') as f:
        for label, count in worker_metrics.items():
            f.write(f'lotus_miner_sealing_{label}{{miner="{miner_id}"}} {count}\n')

def parse_info_for_jobs(info):
    metrics = {
        "computeprooffailed": 0,
        "addpiecefailed": 0,
        "commitfailed": 0,
        "packingfailed": 0,
        "sealprecommit1failed": 0,
        "sealprecommit2failed": 0,
        "commitfinalizedfailed": 0,
        "precommitfailed": 0,
        "finalizedfailed": 0,
        "failedunrecoverable": 0,
        "faultedfinal": 0,
        "removefailed": 0,
        "terminatefailed": 0,
        "removed": 0,
        "precommit1": 0,
        "precommit2": 0,
        "committing": 0,
        "waitseed": 0,
        "waitdeals": 0,
        "addpiece": 0,
        "submitcommitaggregate": 0,
        "commitaggregatewait": 0,
        "commitfinalize": 0,
        "precommitwait": 0,
        "total": 0
    }

    for key in metrics:
        if f"{key.capitalize()}:" in info:
            metrics[key] = int(info.split(f"{key.capitalize()}:")[1].split()[0])

    return metrics

def write_jobs_metrics_to_file(path, miner_id, metrics):
    with open(path, 'a') as f:
        
        for key in metrics:
            if key == "precommit1":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="PC1"}} {metrics[key]}\n')
            elif key == "precommit2":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="PC2"}} {metrics[key]}\n')
            elif key == "committing":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="C2"}} {metrics[key]}\n')
            elif key == "waitseed":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="WS"}} {metrics[key]}\n')
            elif key == "waitdeals":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="WD"}} {metrics[key]}\n')
            elif key == "addpiece":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="AP"}} {metrics[key]}\n')
            elif key == "submitcommitaggregate":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="SCA"}} {metrics[key]}\n')
            elif key == "commitaggregatewait":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="CAW"}} {metrics[key]}\n')
            elif key == "commitfinalize":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="FIN"}} {metrics[key]}\n')
            elif key == "precommitwait":
                f.write(f'lotus_miner_sector_status{{miner="{miner_id}",status="PCW"}} {metrics[key]}\n')
            elif key == "total":
                f.write(f'lotus_miner_sector_status_total{{miner="{miner_id}"}} {metrics["total"]}\n')
            elif key == "computeprooffailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="CP"}} {metrics[key]}\n')
            elif key == "addpiecefailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="AP"}} {metrics[key]}\n')
            elif key == "commitfailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="COM"}} {metrics[key]}\n')
            elif key == "packingfailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="PCK"}} {metrics[key]}\n')
            elif key == "sealprecommit1failed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="PC1"}} {metrics[key]}\n')
            elif key == "sealprecommit2failed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="PC2"}} {metrics[key]}\n')
            elif key == "commitfinalizedfailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="CF"}} {metrics[key]}\n')
            elif key == "precommitfailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="PC"}} {metrics[key]}\n')
            elif key == "finalizedfailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="FIN"}} {metrics[key]}\n')
            elif key == "failedunrecoverable":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="UNR"}} {metrics[key]}\n')
            elif key == "faultedfinal":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="FF"}} {metrics[key]}\n')
            elif key == "removefailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="RM"}} {metrics[key]}\n')
            elif key == "terminatefailed":
                f.write(f'lotus_miner_sector_error{{miner="{miner_id}",status="TER"}} {metrics[key]}\n')
            elif key == "removed":
                f.write(f'lotus_miner_sector_status_removed{{miner="{miner_id}"}} {metrics["removed"]}\n')

def main(config_file):
    config = load_config(config_file)
    set_environment_variables(config)

    miner_id = config['MINER_ID']
    miner_log_file = config['MINER_LOG_FILE']
    path_node_exporter = config['PATH_NODE_EXPORTER']

    disk_paths = config['DISK_PATHS'].split(':')
    disk_labels = config['DISK_LABELS'].split(':')

    if len(disk_paths) != len(disk_labels):
        print("Error: DISK_PATHS and DISK_LABELS must have the same number of elements.")
        sys.exit(1)

    log = subprocess.getoutput(f"tail -n 500 {miner_log_file} | grep 'completed mineOne' | tail -n 1")

    metrics = parse_log_for_metrics(log)
    prom_file_path = f"{path_node_exporter}lotus.{miner_id}.prom.{os.getpid()}"
    write_metrics_to_file(prom_file_path, miner_id, metrics)

    disk_metrics = gather_disk_metrics(disk_paths, disk_labels)
    append_disk_metrics_to_file(prom_file_path, miner_id, disk_metrics)

    subprocess.run("/usr/local/bin/lotus-miner proving deadlines | grep -v -e 'Miner' -e 'deadline' > ./deadlines", shell=True)
    active_sectors, faulty_sectors = process_deadlines("./deadlines")
    write_deadlines_to_file(prom_file_path, miner_id, active_sectors, faulty_sectors)

    for metric_name in ['store', 'seal']:
        subprocess.run(f"/usr/local/bin/lotus-miner storage list | grep -B 2 'Use: {metric_name.capitalize()}' | grep '/' > ./storage", shell=True)
        used_storage, storage_space = calculate_storage_metrics("./storage")
        write_storage_metrics_to_file(prom_file_path, miner_id, metric_name, used_storage, storage_space)

    proving_info = subprocess.getoutput("/usr/local/bin/lotus-miner proving info | grep 'Sectors'")
    in_proving_window = process_proving_window(proving_info)
    write_proving_window_to_file(prom_file_path, miner_id, in_proving_window)

    info = subprocess.getoutput("/usr/local/bin/lotus-miner info")
    balance_metrics = gather_balance_metrics(info)
    write_balance_metrics_to_file(prom_file_path, miner_id, balance_metrics)

    wallets = subprocess.getoutput("/usr/local/bin/lotus-miner actor control list")
    wallet_balances = gather_wallet_balances(wallets)
    write_wallet_balances_to_file(prom_file_path, miner_id, wallet_balances)

    workers = subprocess.getoutput("/usr/local/bin/lotus-miner sealing workers | grep Worker")
    worker_metrics = gather_worker_metrics(workers)
    write_worker_metrics_to_file(prom_file_path, miner_id, worker_metrics)

    jobs_metrics = parse_info_for_jobs(info)
    write_jobs_metrics_to_file(prom_file_path, miner_id, jobs_metrics)

    os.rename(prom_file_path, f"{path_node_exporter}lotus.{miner_id}.prom")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    main(config_file)

