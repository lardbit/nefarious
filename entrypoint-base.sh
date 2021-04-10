# nefarious user and specified uid
RUN_AS_USER=nefarious
RUN_AS_UID=${HOST_DOWNLOAD_UID-1000}

# create if it does not already exist
id -u ${RUN_AS_UID} 2>/dev/null || useradd -u ${RUN_AS_UID} ${RUN_AS_USER}

# set folder permissions
chown -R ${RUN_AS_UID} /app /nefarious-db
