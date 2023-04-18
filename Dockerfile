FROM python:3.8.10
RUN pip install Flask==2.2.2
RUN pip install requests==2.22.0
RUN pip install redis==4.5.1
RUN pip install geopy==2.3.0
RUN pip install matplotlib==3.6.3
COPY scripts /scripts
CMD ["cd","/scripts", "&&","python3", "atx_traffic.py"]