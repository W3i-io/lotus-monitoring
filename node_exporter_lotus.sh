#!/bin/bash
export BOOST_API_INFO="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.9JA_H5KGJfQTAWVqRmC2MVqQ0spTBrXzg5ZNB1M42GM:/ip4/10.200.1.21/tcp/1288/http"
export FULLNODE_API_INFO="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.Z-W88m1ogiMrY4TRjQx4cXBGPY_gp4qQj7H3pfJ0RiE:/ip4/10.200.2.11/tcp/1234/http"
export LOTUS_MINER_PATH="/home/vit/.lotusminer/"
export MARKETS_API_INFO="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJBbGxvdyI6WyJyZWFkIiwid3JpdGUiLCJzaWduIiwiYWRtaW4iXX0.9JA_H5KGJfQTAWVqRmC2MVqQ0spTBrXzg5ZNB1M42GM:/ip4/10.200.1.21/tcp/1288/http"

log=$(tail -n 500 ~/miner202*.log | grep 'completed mineOne' | tail -n 1)

echo $log |  awk -F'["]' '{print "lotus_miner_qap{miner=\"f01896422\"} " $24}' > /var/lib/prometheus/node-exporter/lotus.prom.$$
echo $log |  awk -F'["]' '{print "lotus_network_qap{miner=\"f01896422\"} " $20}' >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo $log | awk -F'[,]' '{print $3}' | awk '{print "lotus_miner_base_epoch{miner=\"f01896422\"} " $2}' >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo $log | awk -F'[,]' '{print $4}' | awk '{print "lotus_miner_base_delta{miner=\"f01896422\"} " $2}' >> /var/lib/prometheus/node-exporter/lotus.prom.$$

eligible=$(echo $log | awk -F'[,]' '{print $11}' | awk '{print $2}')
if test "$eligible" = true
then
 echo "lotus_miner_eligible{miner=\"f01896422\"} 1" >> /var/lib/prometheus/node-exporter/lotus.prom.$$
else
 echo "lotus_miner_eligible{miner=\"f01896422\"} 0" >> /var/lib/prometheus/node-exporter/lotus.prom.$$
fi

#echo "lotus_miner_eligible{miner=\"f01896422\"} "$eligible >> /var/lib/prometheus/node-exporter/lotus.prom.$$

data01=$(df | grep "/dev/mapper/mpathf-part1" | awk '{print $4}')
echo "lotus_miner_data01{miner=\"f01896422\"} "$data01 >> /var/lib/prometheus/node-exporter/lotus.prom.$$
data05=$(df | grep "/dev/mapper/mpathj-part1" | awk '{print $4}')
echo "lotus_miner_data05{miner=\"f01896422\"} "$data05 >> /var/lib/prometheus/node-exporter/lotus.prom.$$
data06=$(df | grep "/dev/mapper/mpathk-part1" | awk '{print $4}')
echo "lotus_miner_data06{miner=\"f01896422\"} "$data06 >> /var/lib/prometheus/node-exporter/lotus.prom.$$
data07=$(df | grep "/dev/mapper/mpathl-part1" | awk '{print $4}')
echo "lotus_miner_data07{miner=\"f01896422\"} "$data07 >> /var/lib/prometheus/node-exporter/lotus.prom.$$


/home/vit/lotus/lotus-miner proving deadlines | grep -v ' 0 (0)\|Miner\|deadline' > /home/vit/deadlines



total_active_sectors=0
total_faulty_sectors=0
total_proving_epochs=0

while IFS= read -r line
do
 active_sectors=$(echo "$line" | awk '{print $4}')
 faulty_sectors=$(echo "$line" | awk '{print $5}' | sed 's/^.\(.*\).$/\1/')
 total_active_sectors=$((total_active_sectors + active_sectors))
 total_faulty_sectors=$((total_faulty_sectors + faulty_sectors))
 total_proving_epochs=$((total_proving_epochs + 60))
done < "/home/vit/deadlines"

echo "lotus_miner_active_sectors{miner=\"f01896422\"} "$total_active_sectors >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_faulty_sectors{miner=\"f01896422\"} "$total_faulty_sectors >> /var/lib/prometheus/node-exporter/lotus.prom.$$

total_used_storage=0
total_storage_space=0

/home/vit/lotus/lotus-miner storage list | grep -B 2 'Use: Store' | grep '/' > /home/vit/storage

while IFS= read -r line
do
 used_space=$(echo "$line" | awk -F']' '{print $2}' | awk '{print $1}')
 space=$(echo "$line" | awk -F']' '{print $2}' | awk '{print $2}' | awk -F/ '{print $2}')
 unit=$(echo "$line" | awk -F']' '{print $2}' | awk '{print $2}' | awk -F/ '{print $1}')
if [[ "$unit" == "GiB" ]]
 then
  used_space=$(echo "scale=2; $used_space * 1073741824" | bc)
 elif [[ "$unit" == "TiB" ]]
 then
  used_space=$(echo "scale=2; $used_space * 1099511627776" | bc)
 else
  used_space=$(echo "scale=2; $used_space * 1125899906842624" | bc)
 fi

 total_unit=$(echo "$line" | awk '{print $5}')

 if [[ "$total_unit" == "GiB" ]]
 then
  space=$(echo "scale=2; $space * 1073741824" | bc)
 elif [[ "$total_unit" == "TiB" ]]
 then
  space=$(echo "scale=2; $space * 1099511627776" | bc)
 else
  space=$(echo "scale=2; $space * 1125899906842624" | bc)
 fi


 total_used_storage=$(echo "scale=2; $total_used_storage + $used_space" | bc)
 total_storage_space=$(echo "scale=2; $total_storage_space + $space" | bc)
done < "/home/vit/storage"

echo "lotus_miner_store_space{miner=\"f01896422\"} "$total_storage_space >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_store_used{miner=\"f01896422\"} "$total_used_storage >> /var/lib/prometheus/node-exporter/lotus.prom.$$


total_used_storage=0
total_storage_space=0

/home/vit/lotus/lotus-miner storage list | grep -B 2 'Use: Seal' | grep '/' > /home/vit/storage

while IFS= read -r line
do
 used_space=$(echo "$line" | awk -F']' '{print $2}' | awk '{print $1}')
 space=$(echo "$line" | awk -F']' '{print $2}' | awk '{print $2}' | awk -F/ '{print $2}')
 unit=$(echo "$line" | awk -F']' '{print $2}' | awk '{print $2}' | awk -F/ '{print $1}')
if [[ "$unit" == "GiB" ]]
 then
  used_space=$(echo "scale=2; $used_space * 1073741824" | bc)
 elif [[ "$unit" == "TiB" ]]
 then
  used_space=$(echo "scale=2; $used_space * 1099511627776" | bc)
 else
  used_space=$(echo "scale=2; $used_space * 1125899906842624" | bc)
 fi

 total_unit=$(echo "$line" | awk '{print $5}')

 if [[ "$total_unit" == "GiB" ]]
 then
  space=$(echo "scale=2; $space * 1073741824" | bc)
 elif [[ "$total_unit" == "TiB" ]]
 then
  space=$(echo "scale=2; $space * 1099511627776" | bc)
 else
  space=$(echo "scale=2; $space * 1125899906842624" | bc)
 fi


 total_used_storage=$(echo "scale=2; $total_used_storage + $used_space" | bc)
 total_storage_space=$(echo "scale=2; $total_storage_space + $space" | bc)
done < "/home/vit/storage"

echo "lotus_miner_seal_space{miner=\"f01896422\"} "$total_storage_space >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_seal_used{miner=\"f01896422\"} "$total_used_storage >> /var/lib/prometheus/node-exporter/lotus.prom.$$

#current_epoch=$(/home/vit/lotus/lotus-miner proving info | grep "Current Epoch" | awk '{print $3}')
#proving_period_start=$(/home/vit/lotus/lotus-miner proving info | grep "Deadline Challenge" | awk '{print $3}')
#proving_period_end=$(/home/vit/lotus/lotus-miner proving info | grep "Deadline Close" | awk '{print $3}')

proving_info=$(/home/vit/lotus/lotus-miner proving info | grep 'Sectors')
#current_epoch=$(echo $proving_info | awk '{print $5}')
#proving_period_start=$(echo $proving_info | awk '{print $13}')
#proving_period_start=$((proving_period_start-20))
#proving_period_end=$(($proving_period_start + 180))
deadline_sectors=$(echo $proving_info | awk '{print $3}')

if [[ $deadline_sectors -gt 0 ]]  
then
 echo "lotus_miner_proving_window{miner=\"f01896422\"} 1" >> /var/lib/prometheus/node-exporter/lotus.prom.$$
else
 echo "lotus_miner_proving_window{miner=\"f01896422\"} 0" >> /var/lib/prometheus/node-exporter/lotus.prom.$$
fi


info=$(/home/vit/lotus/lotus-miner info)

precommit=$(echo $info | awk -F 'PreCommit:' '{print $2}' | awk '{print $1}')
if echo "$precommit > 0" | bc -l | grep -q 1
then
 currency=$(echo $info | awk -F 'PreCommit:' '{print $2}' | awk '{print $2}')
 if test "$currency" = "mFIL"
 then
   precommit=$(echo "scale=4; $precommit / 1000" | bc)
 fi
fi

pledge=$(echo $info | awk -F 'Pledge:' '{print $2}' | awk '{print $1}')
if echo "$pledge > 0" | bc -l | grep -q 1
then
 currency=$( echo $info | awk -F 'Pledge:' '{print $2}' | awk '{print $2}')
 if test "$currency" = "mFIL"
 then
  pledge=$(echo "scale=4; $pledge / 1000" | bc)
 fi
fi

vesting=$( echo $info | awk -F 'Vesting:' '{print $2}' | awk '{print $1}')
if echo "$vesting > 0" | bc -l | grep -q 1
then
 currency=$( echo $info | awk -F 'Vesting:' '{print $2}' | awk '{print $2}')
 if test "$currency" = "mFIL"
 then
   vesting=$(echo "scale=4; $vesting / 1000" | bc)
 fi
fi

market_locked=$( echo $info | awk -F 'Locked:' '{print $2}' | awk '{print $1}')
if echo "$market_locked > 0" | bc -l | grep -q 1
then
 currency=$( echo $info | awk -F 'Locked:' '{print $2}' | awk '{print $2}')
 if test "$currency" = "mFIL"
 then
   market_locked=$(echo "scale=4; $market_locked / 1000" | bc)
 fi
fi

market_available=$( echo $info | awk -F 'Available:' '{print $3}' | awk '{print $1}')
if echo "$market_available > 0" | bc -l | grep -q 1
then
 currency=$( echo $info | awk -F 'Available:' '{print $3}' | awk '{print $2}')
 if test "$currency" = "mFIL"
 then
   market_available=$(echo "scale=4; $market_available / 1000" | bc)
 fi
fi

miner_available=$( echo $info | awk -F 'Available:' '{print $2}' | awk '{print $1}')
if echo "$miner_available > 0" | bc -l | grep -q 1
then
 currency=$( echo $info | awk -F 'Available:' '{print $2}' | awk '{print $2}')
 if test "$currency" = "mFIL"
 then
   miner_available=$(echo "scale=4; $miner_available / 1000" | bc)
 fi
fi

echo "lotus_miner_precommit_balance{miner=\"f01896422\"} "$precommit >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_pledge_balance{miner=\"f01896422\"} "$pledge >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_vesting_balance{miner=\"f01896422\"} "$vesting >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_market_locked_balance{miner=\"f01896422\"} "$market_locked >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_market_available_balance{miner=\"f01896422\"} "$market_available >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_miner_available_balance{miner=\"f01896422\"} "$miner_available >> /var/lib/prometheus/node-exporter/lotus.prom.$$

removed=0
precommit1=0
precommit2=0
committing=0
waitseed=0
waitdeals=0
addpiece=0
submitcommitaggregate=0
total=0
commitaggregatewait=0
commitfinalize=0
precommitwait=0
waitdeals=0

computeprooffailed=0
addpiecefailed=0
commitfailed=0
packingfailed=0
sealprecommit1failed=0
sealprecommit2failed=0
commitfinalizedfailed=0
precommitfailed=0
finalizedfailed=0
failedunrecoverable=0
faultedfinal=0
removefailed=0
terminatefailed=0

terminatewait=0
removing=0
terminating=0
terminatefinality=0

if [[ "$info" == *"ComputerProofFailed:"* ]]
then
 computeprooffailed=$(echo $info | awk -F 'ComputerProofFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"AddPieceFailed:"* ]]
then
 addpiecefailed=$(echo $info | awk -F 'AddPieceFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"CommitFailed:"* ]]
then
 commitfailed=$(echo $info | awk -F 'CommitFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"PackingFailed:"* ]]
then
 packingfailed=$(echo $info | awk -F 'PackingFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"SealPreCommit1Failed:"* ]]
then
 sealprecommit1failed=$(echo $info | awk -F 'SealPreCommit1Failed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"SealPreCommit2Failed:"* ]]
then
 sealprecommit2failed=$(echo $info | awk -F 'SealPreCommit2Failed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"CommitFinalizedFailed:"* ]]
then
 commitfinalizedfailed=$(echo $info | awk -F 'CommitFinalizedFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"PreCommitFailed:"* ]]
then
 precommitfailed=$(echo $info | awk -F 'PreCommitFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"FinalizedFailed:"* ]]
then
 finalizedfailed=$(echo $info | awk -F 'FinalizedFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"FailedUnrecoverable:"* ]]
then
 failedunrecoverable=$(echo $info | awk -F 'FailedUnrecoverable:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"FaultedFinal:"* ]]
then
 faultedfinal=$(echo $info | awk -F 'FaultedFinal:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"RemoveFailed:"* ]]
then
 removefailed=$(echo $info | awk -F 'RemoveFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"TerminateFailed:"* ]]
then
 terminatefailed=$(echo $info | awk -F 'TerminateFailed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"Removed:"* ]]
then
 removed=$(echo $info | awk -F 'Removed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"WaitDeals:"* ]]
then
 waitdeals=$(echo $info | awk -F 'WaitDeals:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"PreCommit1:"* ]]
then
 precommit1=$(echo $info | awk -F 'PreCommit1:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"PreCommitWait:"* ]]
then
 precommitwait=$(echo $info | awk -F 'PreCommitWait:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"PreCommit2:"* ]]
then
 precommit2=$(echo $info | awk -F 'PreCommit2:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"Committing:"* ]]
then
 committing=$(echo $info | awk -F 'Committing:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"WaitSeed:"* ]]
then
 waitseed=$(echo $info | awk -F 'WaitSeed:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"AddPiece:"* ]]
then
 addpiece=$(echo $info | awk -F 'AddPiece:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"SubmitCommitAggregate:"* ]]
then
 submitcommitaggregate=$(echo $info | awk -F 'SubmitCommitAggregate:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"CommitAggregateWait:"* ]]
then
 commitaggregatewait=$(echo $info | awk -F 'CommitAggregateWait:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"CommitFinalize:"* ]]
then
 commitfinalize=$(echo $info | awk -F 'CommitFinalize:' '{print $2}' | awk '{print $1}')
fi

if [[ "$info" == *"Total:"* ]]
then
 total=$(echo $info | awk -F 'Total:' '{print $2}' | awk '{print $1}')
fi


echo "lotus_miner_sector_status_removed{miner=\"f01896422\"} "$removed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"PC1\"} "$precommit1 >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"PC2\"} "$precommit2 >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"C2\"} "$committing >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"WS\"} "$waitseed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"WD\"} "$waitdeals >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"AP\"} "$addpiece >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"SCA\"} "$submitcommitaggregate >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"PCW\"} "$precommitwait >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"CAW\"} "$commitaggregatewait >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status{miner=\"f01896422\",status=\"FIN\"} "$commitfinalize >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_status_total{miner=\"f01896422\"} "$total >> /var/lib/prometheus/node-exporter/lotus.prom.$$

echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"CP\"} "$computeprooffailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"AP\"} "$addpiecefailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"COM\"} "$commitfailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"PCK\"} "$packingfailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"PC1\"} "$sealprecommit1failed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"PC2\"} "$sealprecommit2failed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"CF\"} "$commitfinalizedfailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"PC\"} "$precommitfailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"FIN\"} "$finalizedfailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"FF\"} "$faultedfinal >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"RM\"} "$removefailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"TER\"} "$terminatefailed >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sector_error{miner=\"f01896422\",status=\"UNR\"} "$failedunrecoverable >> /var/lib/prometheus/node-exporter/lotus.prom.$$


wallets=$(/home/vit/lotus/lotus-miner actor control list)

echo "lotus_miner_owner_balance{miner=\"f01896422\"} "$(echo $wallets | awk '{print $9}') >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_worker_balance{miner=\"f01896422\"} "$(echo $wallets | awk '{print $15}') >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_control0_balance{miner=\"f01896422\"} "$(echo $wallets | awk '{print $26}') >> /var/lib/prometheus/node-exporter/lotus.prom.$$

workers=$(/home/vit/lotus/lotus-miner sealing workers | grep Worker)
echo "lotus_miner_sealing_ap_worker{miner=\"f01896422\"} "$(echo -n $workers | grep -Fo _AP | wc -l) >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sealing_pc1_worker{miner=\"f01896422\"} "$(echo -n $workers | grep -Fo _PC1 | wc -l) >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sealing_pc2_worker{miner=\"f01896422\"} "$(echo -n $workers | grep -Fo _PC2 | wc -l) >> /var/lib/prometheus/node-exporter/lotus.prom.$$
echo "lotus_miner_sealing_c2_worker{miner=\"f01896422\"} "$(echo -n $workers | grep -Fo _C2 | wc -l) >> /var/lib/prometheus/node-exporter/lotus.prom.$$