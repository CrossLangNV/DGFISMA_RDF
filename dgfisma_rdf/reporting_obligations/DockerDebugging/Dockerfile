FROM ro-rdf

LABEL maintainer="laurensmeeus93@gmail.com"

RUN apt-get update

### Add SSH server to allow for development within PyCharm
### See https://github.com/rastasheep/ubuntu-sshd/blob/master/18.04/Dockerfile
RUN apt-get --assume-yes install  openssh-server
RUN mkdir /var/run/sshd
RUN echo 'root:root' |chpasswd
RUN sed -ri 's/^#?PermitRootLogin\s+.*/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -ri 's/UsePAM yes/#UsePAM yes/g' /etc/ssh/sshd_config
RUN mkdir /root/.ssh
#RUN mkdir /treebank
#RUN mkdir /neuro-logs
### Add a user for neuro development
RUN useradd --create-home --shell /bin/bash neuro
RUN echo 'neuro:neuro' | chpasswd
#RUN mkdir /home/neuro/python
#RUN mkdir /home/neuro/.pycharm_helpers

CMD ["/usr/sbin/sshd", "-D", "-p", "5000"]
