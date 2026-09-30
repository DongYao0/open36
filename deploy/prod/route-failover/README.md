# Open436 route failover

The monitor keeps the Alibaba Cloud + FRP route primary. After three failed
five-second probes it starts the laboratory `cloudflared` connector. Failback
is deliberately manual and performs five primary probes plus a Cloudflare
edge verification; a failed verification immediately restores the backup.

Commands:

```bash
./open436-route-failover.sh status
./open436-route-failover.sh failover
./open436-route-failover.sh failback
```
