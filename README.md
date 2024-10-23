# sound-cloudripper

[![Python](https://img.shields.io/badge/Python-v3.11-yellow)]()

a (currently outdatedand not functional) tool which basically finds private SoundCloud tracks by bruteforcing shareable links of on.soundcloud.com
```
Shareable SoundCloud links are shortened links, which look like this:
=> on.soundcloud.com/XXXXX => code 302: redirect => soundcloud.com/artist/track
These links can redirect to public tracks as well as private ones too... bruteforce time.

The script catches the redirect and uses a regex to find if the full link contains a private token (public ones do not have any).
If the regex matches, then a private track has been found.

Actually, because of the regex-only filter, there are some false positives:
- Old private tracks that have become public but kept their original shareable link will still have a private token on the link.
- Sometimes deleted tracks may match.

This is easy to fix, though. I just need to do it :')
```

---
##### Educational purposes only, use it at your own risk.
---

### Dependencies
Use `pip install -r requirements.txt` to fulfill these.

---
### Configuration and Setup
The script uses a `config.json` file to save configurations, such as the artist URL, client IDs, threads, and proxy file path. This allows you to save and reuse inputs without having to re-enter them every time.

You can provide a proxy list by selecting a text file in the UI. The file should have the following format:
```
ip,anonymityLevel,asn,country,isp,latency,org,port,protocols,speed,upTime,upTimeSuccessCount,upTimeTryCount,updated_at,responseTime
"5.44.101.53","transparent","AS45012","DE","Alvotech GmbH via velia.net","18","Alvotech GmbH","13128","http","75","100","2","2","2024-10-12T15:14:22.611Z","542"
...
```
The script will use these proxies when making requests to SoundCloud.

---
### Running the Application
The application provides a graphical user interface (GUI) for entering inputs and starting/stopping the script. After running the script, you can:
- Enter the artist URL, client ID(s), number of threads, and proxy file.
- Optionally, test a specific private track URL to verify if it belongs to the selected artist.
- Click the "Start" button to begin the bruteforce process.
- Click the "Stop" button at any time to stop the bruteforce process.

The UI remains responsive, allowing you to interact with it without freezing.

The application should be started using the provided `start.bat` file, which sets up the environment and launches the script.

### Outputs
The script can export the positive results in XML or JSON format.
- **XML Export**: Exports the results to `output.xml` and updates it if it already exists.
- **JSON Export**: Exports the results to `output.json` and updates it if it already exists.

---
### Why Python?
Why not? (I have regrets)
