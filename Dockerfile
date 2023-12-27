FROM amazonlinux:2023

RUN	set -e;						\
	yum -y install tar gzip shadow-utils;		\
	useradd ec2-user;

COPY remote-signer.tar.gz /

RUN	set -e;						\
	mkdir /tmp/build;				\
	cd /tmp/build;					\
	tar -zxvf /remote-signer.tar.gz;		\
	rm /remote-signer.tar.gz;			\
	./scripts/build-package-al2023;			\
	cd /;						\
	rm -rf /tmp/build

ENV PATH /usr/local/sbin:/usr/local/bin:/usr/sbin:\
/usr/bin:/sbin:/bin:/home/ec2-user/.local/bin

#
# The following is a workaround for the fact that pip3 for some
# reason installs PyKCS11 in .local/lib64 which python3.9 can't
# seem to find.

ENV PYTHONPATH /home/ec2-user/.local/lib64/python3.9/site-packages

USER ec2-user
WORKDIR /home/ec2-user
ENTRYPOINT ["/home/ec2-user/.local/bin/signer"]
