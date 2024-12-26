<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
	  <key>Label</key>
	  <string>com.am3</string>
	  <key>UserName</key>
	  <string>{user}</string>
    <key>KeepAlive</key>
    <true/>
	  <key>ProgramArguments</key>
	  <array>
		  <string>/bin/sh</string>
		  <string>-c</string>
		  <string>{am3_executable_path} load</string>
	  </array>
	  <key>RunAtLoad</key>
	  <true/>
	  <key>OnDemand</key>
	  <false/>
	  <key>LaunchOnlyOnce</key>
	  <true/>
	  <key>EnvironmentVariables</key>
    <dict>
      <key>AM3_HOME</key>
      <string>{am3_data_path}</string>
    </dict>
  </dict>
</plist>
