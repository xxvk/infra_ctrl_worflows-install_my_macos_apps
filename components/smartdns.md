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

Local macOS DNS split routing:

- Default/international domains: `1.1.1.1` and `8.8.8.8`
- `.cn` and selected China domains: `114.114.114.114`
- macOS Wi-Fi resolver: `127.0.0.1` and `::1` when IPv6 is bound

## Installation

```bash
brew install smartdns
```

## Configuration

The Homebrew configuration is `/opt/homebrew/etc/smartdns/smartdns.conf`.
The split-routing rules are kept in `/opt/homebrew/etc/smartdns/split-dns.conf`
and included from the main configuration with:

```conf
conf-file /opt/homebrew/etc/smartdns/split-dns.conf
```

The split config binds SmartDNS to `127.0.0.1:53`, defines the global and
China upstream groups, routes `.cn` plus selected domains such as `bilibili.com`
and `hdslb.com` to the China group, and keeps a local cache.

Validate before starting:

```bash
/opt/homebrew/opt/smartdns/sbin/smartdns test \
  -c /opt/homebrew/etc/smartdns/split-dns.conf \
  -d /opt/homebrew/etc/smartdns
```

## Start and activate on macOS

Starting the port-53 service requires the macOS administrator password:

```bash
sudo brew services start smartdns
sudo brew services list | grep smartdns
networksetup -setdnsservers Wi-Fi 127.0.0.1
dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Do not consider SmartDNS effective until `scutil --dns` shows the local
listeners and a normal `dig` query succeeds through them. Record the previous
Wi-Fi DNS values and the rollback command in `state/`; do not put machine DNS
values in this reusable guide.

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
sudo brew services stop smartdns
networksetup -setdnsservers Wi-Fi 192.168.50.1
dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

Before changing the configuration, preserve a copy of both SmartDNS config
files. Never disable Homebrew trust checks or use an unverified DNS mirror.
