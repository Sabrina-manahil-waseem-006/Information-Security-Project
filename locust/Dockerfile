# Use the official Locust image — comes with Python + Locust + web UI ready
FROM locustio/locust:2.32.5

# Copy our scenario file into the image
COPY locustfile.py /mnt/locust/locustfile.py

# Work from the Locust directory so --csv paths are predictable
WORKDIR /mnt/locust