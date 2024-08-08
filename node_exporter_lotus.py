#!/usr/bin/python3

import os
import subprocess
import sys
import re

def set_environment_variables():
    os.environ["BOOST_API_INFO"] = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.9JA_H5KGJfQTAWVqRmC2MVqQ0spTBrXzg5ZNB1M42GM:/ip4/10.200.1.21/tcp/1288/http")
    os.environ["FULLNODE_API_INFO"] = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.Z-W88m1ogiMrY4TRjQx4cXBGPY_gp4qQj7H3pfJ0RiE:/ip4/10.200.2.11/tcp/1234/http")
    os.environ["LOTUS_MINER_PATH"] = "/home/vit/.lotusminer/"
    os.environ["MARKETS_API_INFO"] = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.9JA_H5KGJfQTAWVqRmC2MVqQ0spTBrXzg5ZNB1M42GM:/ip4/10.200.1.21/tcp/1288/http")

def execute_shell_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def write_prometheus_metric(metric_name, value, prom_file):
    with open(prom_file, 'a') as file:
        file.write(f'{metric_name} {value}\n')

def parse_log(log, miner_id, prom_file):
    patterns = [
        (f'lotus_miner_qap{{miner="{miner_id}"}}', r'"([^"]*)"', 24),
        (f'lotus_network_qap{{miner="{miner_id}"}}', r'"([^"]*)"', 20),
        (f'lotus_miner_base_epoch{{miner="{miner_id}"}}', r'([^,]*)', 3),
        (f'lotus_miner_base_delta{{miner="{miner_id}"}}', r'([^,]*)', 4),
    ]
    
    for metric_name, pattern, index in patterns:
        match = re.split(pattern, log)
        if len(match) > index:
            value = match[index]
            write_prometheus_metric(metric_name, value, prom_file)
    
    eligible = re.split(r'[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,([^,]*)', log)[1].strip()
    eligible_value = 1 if eligible == "true" else 0
    write_prometheus_metric(f'lotus_miner_eligible{{miner="{miner_id}"}}', eligible_value, prom_file)

def get_disk_usage(path, metric_name, miner_id, prom_file):
    data = execute_shell_command(f"df | grep '{path}' | awk '{{print $4}}'")
    if data:
        write_prometheus_metric(f'{metric_name}{{miner="{miner_id}"}}', data, prom_file)

def process_proving_deadlines(miner_id, prom_file):
    execute_shell_command("/home/vit/lotus/lotus-miner proving deadlines | grep -v ' 0 (0)\\|Miner\\|deadline' > /home/vit/deadlines")
    with open("/home/vit/deadlines") as file:
        total_active_sectors = 0
        total_faulty_sectors = 0
        total_proving_epochs = 0
        
        for line in file:
            active_sectors = int(line.split()[3])
            faulty_sectors = int(re.sub(r'^\D*(\d+)\D*$', r'\1', line.split()[4]))
            total_active_sectors += active_sectors
            total_faulty_sectors += faulty_sectors
            total_proving_epochs += 60
        
        write_prometheus_metric(f'lotus_miner_active_sectors{{miner="{miner_id}"}}', total_active_sectors, prom_file)
        write_prometheus_metric(f'lotus_miner_faulty_sectors{{miner="{miner_id}"}}', total_faulty_sectors, prom_file)

def process_storage_list(miner_id, prom_file, use_type):
    execute_shell_command(f"/home/vit/lotus/lotus-miner storage list | grep -B 2 'Use: {use_type}' | grep '/' > /home/vit/storage")
    total_used_storage = 0
    total_storage_space = 0
    with open("/home/vit/storage") as file:
        for line in file:
            used_space, space, unit, total_unit = parse_storage_line(line)
            total_used_storage += convert_to_bytes(used_space, unit)
            total_storage_space += convert_to_bytes(space, total_unit)
    
    write_prometheus_metric(f'lotus_miner_{use_type.lower()}_space{{miner="{miner_id}"}}', total_storage_space, prom_file)
    write_prometheus_metric(f'lotus_miner_{use_type.lower()}_used{{miner="{miner_id}"}}', total_used_storage, prom_file)

def parse_storage_line(line):
    parts = line.split(' ')
    used_space = parts[1]
    space = parts[2].split('/')[1]
    unit = parts[2].split('/')[0]
    total_unit = parts[4]
    return used_space, space, unit, total_unit

def convert_to_bytes(size, unit):
    size = float(size)
    if unit == "GiB":
        return size * 1073741824
    elif unit == "TiB":
        return size * 1099511627776
    else:
        return size * 1125899906842624

def main(miner_id):
    set_environment_variables()
    
    prom_file = f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}"
    
    log = execute_shell_command("tail -n 500 ~/miner202*.log | grep 'completed mineOne' | tail -n 1")
    parse_log(log, miner_id, prom_file)
    
    disk_paths = [
        ("/dev/mapper/mpathf-part1", "lotus_miner_data01"),
        ("/dev/mapper/mpathj-part1", "lotus_miner_data05"),
        ("/dev/mapper/mpathk-part1", "lotus_miner_data06"),
        ("/dev/mapper/mpathl-part1", "lotus_miner_data07")
    ]
    
    for path, metric_name in disk_paths:
        get_disk_usage(path, metric_name, miner_id, prom_file)
    
    process_proving_deadlines(miner_id, prom_file)
    process_storage_list(miner_id, prom_file, "Store")
    process_storage_list(miner_id, prom_file, "Seal")
    
    # Process proving info
    proving_info = execute_shell_command("/home/vit/lotus/lotus-miner proving info | grep 'Sectors'")
    deadline_sectors = int(proving_info.split()[2])
    
    if deadline_sectors > 0:
        write_prometheus_metric(f'lotus_miner_proving_window{{miner="{miner_id}"}}', 1, prom_file)
    else:
        write_prometheus_metric(f'lotus_miner_proving_window{{miner="{miner_id}"}}', 0, prom_file)
    
    # Process miner info
    miner_info = execute_shell_command("/home/vit/lotus/lotus-miner info")
    balances = parse_miner_balances(miner_info, miner_id)
    
    for metric_name, value in balances.items():
        write_prometheus_metric(metric_name, value, prom_file)
    
    # Process control list
    wallets = execute_shell_command("/home/vit/lotus/lotus-miner actor control list")
    write_prometheus_metric(f'lotus_miner_owner_balance{{miner="{miner_id}"}}', extract_value_from_log(wallets, r'\S+', 8), prom_file)
    write_prometheus_metric(f'lotus_miner_worker_balance{{miner="{miner_id}"}}', extract_value_from_log(wallets, r'\S+', 14), prom_file)
    write_prometheus_metric(f'lotus_miner_control0_balance{{miner="{miner_id}"}}', extract_value_from_log(wallets, r'\S+', 25), prom_file)
    
    # Process sealing workers
    workers = execute_shell_command("/home/vit/lotus/lotus-miner sealing workers | grep Worker")
    write_prometheus_metric(f'lotus_miner_sealing_ap_worker{{miner="{miner_id}"}}', workers.count('_AP'), prom_file)
    write_prometheus_metric(f'lotus_miner_sealing_pc1_worker{{miner="{miner_id}"}}', workers.count('_PC1'), prom_file)
    write_prometheus_metric(f'lotus_miner_sealing_pc2_worker{{miner="{miner_id}"}}', workers.count('_PC2'), prom_file)
    write_prometheus_metric(f'lotus_miner_sealing_c2_worker{{miner="{miner_id}"}}', workers.count('_C2'), prom_file)
    
    # Rename the temporary Prometheus file
    os.rename(prom_file, "/var/lib/prometheus/node-exporter/lotus.prom")

def parse_miner_balances(info, miner_id):
    balances = {
        f'lotus_miner_precommit_balance{{miner="{miner_id}"}}': extract_balance(info, 'PreCommit:'),
        f'lotus_miner_pledge_balance{{miner="{miner_id}"}}': extract_balance(info, 'Pledge:'),
        f'lotus_miner_vesting_balance{{miner="{miner_id}"}}': extract_balance(info, 'Vesting:'),
        f'lotus_miner_market_locked_balance{{miner="{miner_id}"}}': extract_balance(info, 'Locked:'),
        f'lotus_miner_market_available_balance{{miner="{miner_id}"}}': extract_balance(info, 'Available:', 2),
        f'lotus_miner_miner_available_balance{{miner="{miner_id}"}}': extract_balance(info, 'Available:')
    }
    return balances

def extract_balance(info, field, position=1):
    match = re.search(fr'{field}\s+(\S+)', info)
    if match:
        balance = float(match.group(1))
        currency = info.split()[position + 1]
        if currency == "mFIL":
            return balance / 1000
        return balance
    return 0

def extract_value_from_log(log, pattern, position):
    match = re.findall(pattern, log)
    if match and len(match) > position:
        return match[position]
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <MINER_ID>")
        sys.exit(1)
    
    miner_id = sys.argv[1]
    main(miner_id)
