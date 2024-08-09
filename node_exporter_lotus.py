#!/usr/bin/python3

import os
import subprocess

os.environ['BOOST_API_INFO'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.9JA_H5KGJfQTAWVqRmC2MVqQ0spTBrXzg5ZNB1M42GM:/ip4/10.200.1.21/tcp/1288/http"
os.environ['FULLNODE_API_INFO'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.Z-W88m1ogiMrY4TRjQx4cXBGPY_gp4qQj7H3pfJ0RiE:/ip4/10.200.2.11/tcp/1234/http"
os.environ['LOTUS_MINER_PATH'] = "/home/vit/.lotusminer/"
os.environ['MARKETS_API_INFO'] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.9JA_H5KGJfQTAWVqRmC2MVqQ0spTBrXzg5ZNB1M42GM:/ip4/10.200.1.21/tcp/1288/http"

log = subprocess.getoutput("tail -n 500 ~/miner202*.log | grep 'completed mineOne' | tail -n 1")

with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'w') as f:
    f.write(f"lotus_miner_qap{{miner=\"f01896422\"}} {log.split('\"')[23]}\n")
    f.write(f"lotus_network_qap{{miner=\"f01896422\"}} {log.split('\"')[19]}\n")
    f.write(f"lotus_miner_base_epoch{{miner=\"f01896422\"}} {log.split(',')[2].split()[1]}\n")
    f.write(f"lotus_miner_base_delta{{miner=\"f01896422\"}} {log.split(',')[3].split()[1]}\n")

eligible = log.split(',')[10].split()[1]
if eligible == "true":
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write("lotus_miner_eligible{miner=\"f01896422\"} 1\n")
else:
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write("lotus_miner_eligible{miner=\"f01896422\"} 0\n")

data01 = subprocess.getoutput("df | grep '/dev/mapper/mpathf-part1'").split()[3]
with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_data01{{miner=\"f01896422\"}} {data01}\n")

data05 = subprocess.getoutput("df | grep '/dev/mapper/mpathj-part1'").split()[3]
with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_data05{{miner=\"f01896422\"}} {data05}\n")

data06 = subprocess.getoutput("df | grep '/dev/mapper/mpathk-part1'").split()[3]
with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_data06{{miner=\"f01896422\"}} {data06}\n")

data07 = subprocess.getoutput("df | grep '/dev/mapper/mpathl-part1'").split()[3]
with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_data07{{miner=\"f01896422\"}} {data07}\n")

subprocess.run("/home/vit/lotus/lotus-miner proving deadlines | grep -v ' 0 (0)|Miner|deadline' > /home/vit/deadlines", shell=True)

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
    f.write(f"lotus_miner_active_sectors{{miner=\"f01896422\"}} {total_active_sectors}\n")
    f.write(f"lotus_miner_faulty_sectors{{miner=\"f01896422\"}} {total_faulty_sectors}\n")

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
    f.write(f"lotus_miner_store_space{{miner=\"f01896422\"}} {total_storage_space}\n")
    f.write(f"lotus_miner_store_used{{miner=\"f01896422\"}} {total_used_storage}\n")

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
    f.write(f"lotus_miner_seal_space{{miner=\"f01896422\"}} {total_storage_space}\n")
    f.write(f"lotus_miner_seal_used{{miner=\"f01896422\"}} {total_used_storage}\n")

proving_info = subprocess.getoutput("/home/vit/lotus/lotus-miner proving info | grep 'Sectors'")
deadline_sectors = int(proving_info.split()[2])

if deadline_sectors > 0:
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write("lotus_miner_proving_window{miner=\"f01896422\"} 1\n")
else:
    with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
        f.write("lotus_miner_proving_window{miner=\"f01896422\"} 0\n")

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
    f.write(f"lotus_miner_precommit_balance{{miner=\"f01896422\"}} {precommit}\n")
    f.write(f"lotus_miner_pledge_balance{{miner=\"f01896422\"}} {pledge}\n")
    f.write(f"lotus_miner_vesting_balance{{miner=\"f01896422\"}} {vesting}\n")
    f.write(f"lotus_miner_market_locked_balance{{miner=\"f01896422\"}} {market_locked}\n")
    f.write(f"lotus_miner_market_available_balance{{miner=\"f01896422\"}} {market_available}\n")
    f.write(f"lotus_miner_miner_available_balance{{miner=\"f01896422\"}} {miner_available}\n")

computeprooffailed = 0
addpiecefailed = 0
commitfailed = 0
packingfailed = 0
sealprecommit1failed = 0
sealprecommit2failed = 0
commitfinalizedfailed = 0
precommitfailed = 0
finalizedfailed = 0
failedunrecoverable = 0
faultedfinal = 0
removefailed = 0
terminatefailed = 0

terminatewait = 0
removing = 0
terminating = 0
terminatefinality = 0

if "ComputerProofFailed:" in info:
    computeprooffailed = int(info.split('ComputerProofFailed:')[1].split()[0])

if "AddPieceFailed:" in info:
    addpiecefailed = int(info.split('AddPieceFailed:')[1].split()[0])

if "CommitFailed:" in info:
    commitfailed = int(info.split('CommitFailed:')[1].split()[0])

if "PackingFailed:" in info:
    packingfailed = int(info.split('PackingFailed:')[1].split()[0])

if "SealPreCommit1Failed:" in info:
    sealprecommit1failed = int(info.split('SealPreCommit1Failed:')[1].split()[0])

if "SealPreCommit2Failed:" in info:
    sealprecommit2failed = int(info.split('SealPreCommit2Failed:')[1].split()[0])

if "CommitFinalizedFailed:" in info:
    commitfinalizedfailed = int(info.split('CommitFinalizedFailed:')[1].split()[0])

if "PreCommitFailed:" in info:
    precommitfailed = int(info.split('PreCommitFailed:')[1].split()[0])

if "FinalizedFailed:" in info:
    finalizedfailed = int(info.split('FinalizedFailed:')[1].split()[0])

if "FailedUnrecoverable:" in info:
    failedunrecoverable = int(info.split('FailedUnrecoverable:')[1].split()[0])

if "FaultedFinal:" in info:
    faultedfinal = int(info.split('FaultedFinal:')[1].split()[0])

if "RemoveFailed:" in info:
    removefailed = int(info.split('RemoveFailed:')[1].split()[0])

if "TerminateFailed:" in info:
    terminatefailed = int(info.split('TerminateFailed:')[1].split()[0])

if "Removed:" in info:
    removed = int(info.split('Removed:')[1].split()[0])

if "WaitDeals:" in info:
    waitdeals = int(info.split('WaitDeals:')[1].split()[0])

if "PreCommit1:" in info:
    precommit1 = int(info.split('PreCommit1:')[1].split()[0])

if "PreCommitWait:" in info:
    precommitwait = int(info.split('PreCommitWait:')[1].split()[0])

if "PreCommit2:" in info:
    precommit2 = int(info.split('PreCommit2:')[1].split()[0])

if "Committing:" in info:
    committing = int(info.split('Committing:')[1].split()[0])

if "WaitSeed:" in info:
    waitseed = int(info.split('WaitSeed:')[1].split()[0])

if "AddPiece:" in info:
    addpiece = int(info.split('AddPiece:')[1].split()[0])

if "SubmitCommitAggregate:" in info:
    submitcommitaggregate = int(info.split('SubmitCommitAggregate:')[1].split()[0])

if "CommitAggregateWait:" in info:
    commitaggregatewait = int(info.split('CommitAggregateWait:')[1].split()[0])

if "CommitFinalize:" in info:
    commitfinalize = int(info.split('CommitFinalize:')[1].split()[0])

if "Total:" in info:
    total = int(info.split('Total:')[1].split()[0])

with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_sector_status_removed{{miner=\"f01896422\"}} {removed}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"PC1\"}} {precommit1}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"PC2\"}} {precommit2}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"C2\"}} {committing}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"WS\"}} {waitseed}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"WD\"}} {waitdeals}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"AP\"}} {addpiece}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"SCA\"}} {submitcommitaggregate}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"PCW\"}} {precommitwait}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"CAW\"}} {commitaggregatewait}\n")
    f.write(f"lotus_miner_sector_status{{miner=\"f01896422\",status=\"FIN\"}} {commitfinalize}\n")
    f.write(f"lotus_miner_sector_status_total{{miner=\"f01896422\"}} {total}\n")

    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"CP\"}} {computeprooffailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"AP\"}} {addpiecefailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"COM\"}} {commitfailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"PCK\"}} {packingfailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"PC1\"}} {sealprecommit1failed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"PC2\"}} {sealprecommit2failed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"CF\"}} {commitfinalizedfailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"PC\"}} {precommitfailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"FIN\"}} {finalizedfailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"FF\"}} {faultedfinal}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"RM\"}} {removefailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"TER\"}} {terminatefailed}\n")
    f.write(f"lotus_miner_sector_error{{miner=\"f01896422\",status=\"UNR\"}} {failedunrecoverable}\n")

wallets = subprocess.getoutput("/home/vit/lotus/lotus-miner actor control list")

with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_owner_balance{{miner=\"f01896422\"}} {wallets.split()[8]}\n")
    f.write(f"lotus_miner_worker_balance{{miner=\"f01896422\"}} {wallets.split()[14]}\n")
    f.write(f"lotus_miner_control0_balance{{miner=\"f01896422\"}} {wallets.split()[25]}\n")

workers = subprocess.getoutput("/home/vit/lotus/lotus-miner sealing workers | grep Worker")
with open(f"/var/lib/prometheus/node-exporter/lotus.prom.{os.getpid()}", 'a') as f:
    f.write(f"lotus_miner_sealing_ap_worker{{miner=\"f01896422\"}} {workers.count('_AP')}\n")
    f.write(f"lotus_miner_sealing_pc1_worker{{miner=\"f01896422\"}} {workers.count('_PC1')}\n")
    f.write(f"lotus_miner_sealing_pc2_worker{{miner=\"f01896422\"}} {workers.count('_PC2')}\n")
    f.write(f"lotus_miner_sealing_c2_worker{{miner=\"f01896422\"}} {workers.count('_C2')}\n")
