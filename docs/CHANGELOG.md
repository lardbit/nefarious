4/10/21
- Updated transmission **internal** download path to `/downloads/`.  Previously it was `/downloads/completed`.  This won't affect existing users unless you update `transmission-settings.json` and/or `docker-compose-base.yml` from GitHub.
- Subtitles are now (optionally) downloaded via celery which will be running as `root` if you haven't updated your `docker-compose.base.yml` to use the new entrypoint which will otherwise run it as a non-privileged user.
