class Quality:
    Unknown = 'unknown'
    SDTV = 'sdtv'
    DVD = 'dvd'
    HDTV720p = 'hd720p'
    Bluray720p = 'bluray720p'


media_extensions = [
    # Unknown
    {".webm", Quality.Unknown},

    # SDTV
    {".m4v", Quality.SDTV},
    {".3gp", Quality.SDTV},
    {".nsv", Quality.SDTV},
    {".ty", Quality.SDTV},
    {".strm", Quality.SDTV},
    {".rm", Quality.SDTV},
    {".rmvb", Quality.SDTV},
    {".m3u", Quality.SDTV},
    {".ifo", Quality.SDTV},
    {".mov", Quality.SDTV},
    {".qt", Quality.SDTV},
    {".divx", Quality.SDTV},
    {".xvid", Quality.SDTV},
    {".bivx", Quality.SDTV},
    {".nrg", Quality.SDTV},
    {".pva", Quality.SDTV},
    {".wmv", Quality.SDTV},
    {".asf", Quality.SDTV},
    {".asx", Quality.SDTV},
    {".ogm", Quality.SDTV},
    {".ogv", Quality.SDTV},
    {".m2v", Quality.SDTV},
    {".avi", Quality.SDTV},
    {".bin", Quality.SDTV},
    {".dat", Quality.SDTV},
    {".dvr-ms", Quality.SDTV},
    {".mpg", Quality.SDTV},
    {".mpeg", Quality.SDTV},
    {".mp4", Quality.SDTV},
    {".avc", Quality.SDTV},
    {".vp3", Quality.SDTV},
    {".svq3", Quality.SDTV},
    {".nuv", Quality.SDTV},
    {".viv", Quality.SDTV},
    {".dv", Quality.SDTV},
    {".fli", Quality.SDTV},
    {".flv", Quality.SDTV},
    {".wpl", Quality.SDTV},

    # DVD
    {".img", Quality.DVD},
    {".iso", Quality.DVD},
    {".vob", Quality.DVD},

    # HD
    {".mkv", Quality.HDTV720p},
    {".ts", Quality.HDTV720p},
    {".wtv", Quality.HDTV720p},

    # Bluray
    {".m2ts", Quality.Bluray720p}
]