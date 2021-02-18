
# set base image (host OS)
FROM python:3.8

LABEL maintainer="laurensmeeus93@gmail.com"

# set the working directory in the container
WORKDIR /tmp

# copy the dependencies file to the working directory
COPY docker/requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# ~~~ Remote SSH ~~~

RUN apt-get update

### Add SSH server to allow for development within PyCharm
### See https://github.com/rastasheep/ubuntu-sshd/blob/master/18.04/Dockerfile
RUN apt-get --assume-yes install  openssh-server
RUN mkdir /var/run/sshd
RUN echo 'root:root' |chpasswd
RUN sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config
RUN mkdir /root/.ssh
### Add a user for neuro development
RUN useradd --create-home --shell /bin/bash neuro
RUN echo 'neuro:neuro' | chpasswd

CMD ["/usr/sbin/sshd", "-D", "-p", "5000"]
