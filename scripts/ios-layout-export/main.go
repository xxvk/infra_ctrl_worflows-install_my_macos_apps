// ios-layout-export: read the iPhone home-screen layout via go-ios
// SpringBoard getIconState and emit Markdown for repository storage.
//
// Usage: go run . [--udid=<UDID>] [--output=layout.md]
package main

import (
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/danielpaulus/go-ios/ios"
	"github.com/danielpaulus/go-ios/ios/springboard"
)

func main() {
	udid := flag.String("udid", "", "target device UDID (default: first connected)")
	output := flag.String("output", "iphone-home-layout.md", "output Markdown path")
	flag.Parse()

	// 1. enumerate devices
	list, err := ios.ListDevices()
	if err != nil {
		fmt.Fprintf(os.Stderr, "error listing devices: %v\n", err)
		os.Exit(1)
	}
	if len(list.DeviceList) == 0 {
		fmt.Fprintln(os.Stderr, "no devices connected")
		os.Exit(1)
	}
	var device ios.DeviceEntry
	if *udid != "" {
		found := false
		for _, d := range list.DeviceList {
			if d.Properties.SerialNumber == *udid {
				device = d
				found = true
				break
			}
		}
		if !found {
			fmt.Fprintf(os.Stderr, "device %s not found\n", *udid)
			os.Exit(1)
		}
	} else {
		device = list.DeviceList[0]
	}
	deviceName := deviceNameOf(device)

	// 2. open springboard and read layout
	client, err := springboard.NewClient(device)
	if err != nil {
		fmt.Fprintf(os.Stderr, "could not connect to springboard: %v\n", err)
		os.Exit(1)
	}
	defer client.Close()

	screens, err := client.ListIcons()
	if err != nil {
		fmt.Fprintf(os.Stderr, "could not read icon state: %v\n", err)
		os.Exit(1)
	}

	// 3. render Markdown
	var b strings.Builder
	b.WriteString("# iPhone home screen layout\n\n")
	b.WriteString(fmt.Sprintf("- Device: `%s`\n", deviceName))
	b.WriteString(fmt.Sprintf("- Generated: go-ios springboard getIconState\n"))
	b.WriteString(fmt.Sprintf("- Screens: %d (index 0 = dock)\n\n", len(screens)))

	for i, screen := range screens {
		title := fmt.Sprintf("Screen %d", i)
		if i == 0 {
			title = "Dock (screen 0)"
		}
		b.WriteString(fmt.Sprintf("## %s\n\n", title))
		b.WriteString("| # | Name | Type | Bundle ID / URL |\n")
		b.WriteString("|---|---|---|---|\n")
		for j, icon := range screen {
			name, kind, detail := describe(icon)
			b.WriteString(fmt.Sprintf("| %d | %s | %s | %s |\n", j+1, esc(name), kind, esc(detail)))
		}
		b.WriteString("\n")
	}

	// 4. write output
	if err := os.WriteFile(*output, []byte(b.String()), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write error: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("layout written to %s (%d screens)\n", *output, len(screens))
}

// deviceNameOf returns the UDID plus the friendly DeviceName when available.
func deviceNameOf(d ios.DeviceEntry) string {
	name := d.Properties.SerialNumber
	if resp, err := ios.GetValues(d); err == nil {
		if n := resp.Value.DeviceName; n != "" {
			name = n + " (" + d.Properties.SerialNumber + ")"
		}
	}
	return name
}

// describe turns an Icon into (name, kind, detail).
func describe(icon springboard.Icon) (string, string, string) {
	switch v := icon.(type) {
	case springboard.AppIcon:
		return v.Name, "App", v.BundleId
	case springboard.WebClip:
		return v.Name, "WebClip", v.URL
	case springboard.Folder:
		return v.Name, "Folder", folderSummary(v)
	case springboard.Custom:
		return "(widget)", "Widget", "custom (details not exposed by SpringBoard)"
	default:
		return fmt.Sprintf("%T", icon), "Unknown", ""
	}
}

func folderSummary(f springboard.Folder) string {
	total := 0
	for _, page := range f.Icons {
		total += len(page)
	}
	return fmt.Sprintf("folder with %d icons across %d pages", total, len(f.Icons))
}

func esc(s string) string {
	s = strings.ReplaceAll(s, "|", "\\|")
	return s
}
