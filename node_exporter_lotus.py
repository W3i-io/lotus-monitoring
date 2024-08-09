#!/usr/bin/python3

import os
import subprocess
import configparser
import sys

def set_environment_variables(config):
    """Set environment variables based on the configuration."""
    os.environ['BOOST_API_INFO'] = config['DEFAULT']['BOOST_API_INFO']
    os.environ['FULLNODE_API_INFO'] = config['DEFAULT']['FULLNODE_API_INFO']
    os.environ['LOTUS_MINER_PATH'] = config['DEFAULT']['LOTUS_MINER_PATH']
    os.environ['MARKETS_API_INFO'] = config['DEFAULT']['MARKETS_API_INFO']

def parse_log_file(log_file):
    """Extract relevant metrics from the miner log file."""
    log = subprocess.getoutput(f"tail -n 500 {log_file} | grep 'completed mineOne' | tail -n 1")
    miner_qap = log.split("\"")[23]
    network_qap = log.split("\"")[19]
    base_epoch = log.split(",")[2].split()[1]
    base_delta = log.split(",")[3].split()[1]
    eligible = log.split(',')[10].split()[1]
    return miner_qap, network_qap, base_epoch, base_delta, eligible

def write_prometheus_metrics(file_path, miner_id, metrics):
    """Write the extracted metrics to the Prometheus file."""
    with open(file_path, 'a') as f:
        for key, value in metrics.items():
            f.write(f'{key}{{miner="{miner_id}"}} {value}\n')

def gather_disk_statistics(disk_paths, disk_labels):
    """Gather disk statistics for each path and label."""
    metrics = {}
    for path, label in zip(disk_paths, disk_labels):
        data = subprocess.getoutput(f"df | grep '{path}'").split()[3]
        metrics[f'lotus_miner_{label}'] = data
    return metrics

def parse_deadlines():
    """Parse the deadlines file and calculate active and faulty sectors."""
    subprocess.run("lotus-miner proving deadlines | grep -v -e 'Miner' -e 'deadline' > ./deadlines", shell=True)
    
    total_active_sectors, total_faulty_sectors = 0, 0
    
    with open("./deadlines", 'r') as file:
        for line in file:
            active_sectors = int(line.split()[3])
            faulty_sectors = int(line.split()[4].strip("()"))
            total_active_sectors += active_sectors
            total_faulty_sectors += faulty_sectors
    
    return total_active_sectors, total_faulty_sectors

def parse_storage_statistics(storage_type):
    """Parse storage statistics for given storage type ('Store' or 'Seal')."""
    subprocess.run(f"lotus-miner storage list | grep -B 2 'Use: {storage_type}' | grep '/' > ./storage", shell=True)
    
    total_used_storage, total_storage_space = 0, 0
    
    with open("./storage", 'r') as file:
        for line in file:
            used_space = float(line.split(']')[1].split()[0])
            space = float(line.split(']')[1].split()[1].split('/')[1])
            unit = line.split(']')[1].split()[1].split('/')[0]
            total_unit = line.split()[4]
            
            used_space *= get_unit_multiplier(unit)
            space *= get_unit_multiplier(total_unit)
            
            total_used_storage += used_space
            total_storage_space += space
    
    return total_storage_space, total_used_storage

def get_unit_multiplier(unit):
    """Get the multiplier for storage units."""
    if unit == "GiB":
        return 1073741824
    elif unit == "TiB":
        return 1099511627776
    else:
        return 1125899906842624

def main(config_file):
    # Parse the configuration file
    config = configparser.ConfigParser()
    config.read(config_file)

    # Set environment variables
    set_environment_variables(config)
    
    miner_id = config['DEFAULT']['MINER_ID']
    miner_log_file = config['DEFAULT']['MINER_LOG_FILE']
    path_node_exporter = config['DEFAULT']['PATH_NODE_EXPORTER']
    
    # Get disk paths and labels from config
    disk_paths = config['DEFAULT']['DISK_PATHS'].split(':')
    disk_labels = config['DEFAULT']['DISK_LABELS'].split(':')

    # Ensure that disk_paths and disk_labels have the same length
    if len(disk_paths) != len(disk_labels):
        print("Error: DISK_PATHS and DISK_LABELS must have the same number of elements.")
        sys.exit(1)

    prom_file_path = f"{path_node_exporter}lotus.{miner_id}.prom.{os.getpid()}"

    # Parse log file for metrics
    miner_qap, network_qap, base_epoch, base_delta, eligible = parse_log_file(miner_log_file)
    
    metrics = {
        'lotus_miner_qap': miner_qap,
        'lotus_network_qap': network_qap,
        'lotus_miner_base_epoch': base_epoch,
        'lotus_miner_base_delta': base_delta,
        'lotus_miner_eligible': '1' if eligible == "true" else '0'
    }
    
    # Write basic metrics to file
    write_prometheus_metrics(prom_file_path, miner_id, metrics)
    
    # Gather disk statistics and write to file
    disk_metrics = gather_disk_statistics(disk_paths, disk_labels)
    write_prometheus_metrics(prom_file_path, miner_id, disk_metrics)
    
    # Parse deadlines and write sector metrics to file
    total_active_sectors, total_faulty_sectors = parse_deadlines()
    
    sector_metrics = {
        'lotus_miner_active_sectors': total_active_sectors,
        'lotus_miner_faulty_sectors': total_faulty_sectors
    }
    
    write_prometheus_metrics(prom_file_path, miner_id, sector_metrics)
    
    # Parse storage statistics for both Store and Seal and write to file
    store_space, store_used = parse_storage_statistics('Store')
    seal_space, seal_used = parse_storage_statistics('Seal')
    
    storage_metrics = {
        'lotus_miner_store_space': store_space,
        'lotus_miner_store_used': store_used,
        'lotus_miner_seal_space': seal_space,
        'lotus_miner_seal_used': seal_used
    }
    
    write_prometheus_metrics(prom_file_path, miner_id, storage_metrics)
    
    # Additional processing (e.g., proving info, balance checks) would follow the same pattern
    
    os.rename(prom_file_path, f"{path_node_exporter}lotus.{miner_id}.prom")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    main(config_file)
