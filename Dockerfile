FROM ubuntu:22.04

COPY . /root/showroom-recorder

WORKDIR /root/showroom-recorder

RUN apt update

RUN apt install -y ffmpeg python3-pip
 
RUN pip install showroom-recorder


