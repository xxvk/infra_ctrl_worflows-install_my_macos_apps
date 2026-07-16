---
component_id: "smartdns"
name: "SmartDNS"
category: "Network CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "smartdns"
official_url: "https://github.com/mokeyish/smartdns-rs"
check_command: "smartdns"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 20000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/bin/smartdns"
---
# SmartDNS

## Purpose

Local macOS DNS proxy. Split routing is optional and must be explicitly
configured; installing SmartDNS alone must not silently change domain routing.

## Installation

```bash
brew install smartdns
```

## Configuration

The Homebrew configuration is `/opt/homebrew/etc/smartdns/smartdns.conf`.
The reusable baseline template is `config/smartdns.conf`. If split-routing is
needed, create and review a separate `split-dns.conf` and include it from the
main configuration with:

```conf
conf-file /opt/homebrew/etc/smartdns/split-dns.conf
```

The baseline binds `127.0.0.1:53` and `[::1]:53` and uses the previously
approved upstream DNS values. Do not claim split routing is active unless the
included configuration and a domain-specific query prove it.

Validate before starting:

```bash
/opt/homebrew/opt/smartdns/sbin/smartdns test \
  -c /opt/homebrew/etc/smartdns/split-dns.conf \
  -d /opt/homebrew/etc/smartdns
```

## Start and activate on macOS

Starting the port-53 service requires the macOS administrator password. Prefer
the system LaunchDaemon so the service survives logout and reboot:

```bash
sudo smartdns service install
sudo smartdns service start
launchctl print system/homebrew.mxcl.smartdns
networksetup -setdnsservers <active-service> 127.0.0.1 ::1
dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Before starting, inspect and disable a duplicate user LaunchAgent at
`~/Library/LaunchAgents/homebrew.mxcl.smartdns.plist`; keep a backup in
`state/` and retain only the system LaunchDaemon. A duplicate user agent can
produce Homebrew `error 101` while the system daemon is healthy.

Do not consider SmartDNS effective until `launchctl print system/homebrew.mxcl.smartdns`
shows `state = running`, `scutil --dns` shows the local listeners, and a normal
`dig` query succeeds through them. Record the previous DNS values, changed
network service, listener addresses, service status, and rollback command in
`state/`; do not put machine DNS values in this reusable guide.

## Verification

```bash
scutil --dns | grep nameserver
dig @127.0.0.1 example.com A
dig @127.0.0.1 dl.hdslb.com A
dig +short example.com A
```

Both queries should report `SERVER: 127.0.0.1#53`; the first uses the global
group and the second uses the China rule.

## Rollback

```bash
sudo smartdns service stop
networksetup -setdnsservers <active-service> <previous-dns-1> <previous-dns-2>
dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Before changing the configuration, preserve a copy of both SmartDNS config
files. Never disable Homebrew trust checks or use an unverified DNS mirror.
