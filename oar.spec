%define version 1.6.2
%define release %mkrel 14
%define wwwdir /var/www/html
	
Name:		oar
Version:	%{version}
Release:	%{release}
Summary:	OAR Batch Scheduler
License:	GPL
Group:		System/Servers
Url:		http://oar.imag.fr
Source0:	oar_%{version}-rc2.tar.gz
Source1:	oar_job.sh
Source2:	oar-server
Patch0:		oar_1.6_rc2.patch
Patch1: 	oar_makefile.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}

%description 
This is OAR Batch Scheduler

%package common
Summary:	OAR batch scheduler common package
Group:		System/Servers
BuildArch: 	noarch
Requires:	sudo, perl-DBD-mysql, openssh-clients, openssh-server
provides: 	perl(oar_iolib)

%description common
This package installs the server part or the OAR batch scheduler

%package server
Summary:	OAR batch scheduler server package
Group:		System/Servers
Requires:	oar-common = %version-%release, fping, nmap
BuildArch: 	noarch

%description server
This package installs the server part or the OAR batch scheduler

%package user
Summary:	OAR batch scheduler node package
Group:		System/Servers
Requires:	oar-common = %version-%release
BuildArch: 	noarch

%description user
This package install the submition and query part or the OAR batch scheduler

%package node
Summary:	OAR batch scheduler node package
Group:		System/Servers
Requires:	oar-common = %version-%release
BuildArch: 	noarch

%description node
This package installs the execution node part or the OAR batch scheduler

%package draw-gantt
Summary:	OAR batch scheduler Gantt reservation diagram
Group:		System/Servers
Requires:	oar-common = %version-%release, oar-user = %version-%release, monika
BuildArch: 	noarch
requires: apache

%description draw-gantt
This package install the OAR batch scheduler Gantt reservation diagram CGI

%package desktop-computing-cgi
Summary:	OAR batch scheduler desktop computing CGI
Group:		System/Servers
Requires:	oar-common = %version-%release
BuildArch: 	noarch
requires: apache

%description desktop-computing-cgi
This package install the OAR batch scheduler desktop computing CGI

%package desktop-computing-agent
Summary:	OAR batch scheduler desktop computing Agent
Group:		System/Servers
Requires:	oar-common = %version-%release
BuildArch: 	noarch
requires: apache

%description desktop-computing-agent
This package install the OAR batch scheduler desktop computing Agent

%package doc
Summary:	OAR batch scheduler documentation package
Group:		Books/Computer books
BuildArch: 	noarch

%description doc
This package install some documentation for OAR batch scheduler

%prep
%setup -q -n 1.6
%patch0 -p1
%patch1 -p1
%build

%install
%__rm -rf %buildroot
# Dumb install needed to create file lists
mkdir -p $RPM_BUILD_ROOT/var/lib/oar
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/profile.d/

#/usr/lib/perl5/vendor_perl/5.8.7/"
cat > $RPM_BUILD_ROOT/%{_sysconfdir}/profile.d/oar.sh <<EOF
#!/bin/sh
export OARDIR="%{perl_vendorlib}" 
EOF

%make PREFIX=$RPM_BUILD_ROOT/usr OARUSER=root OARGROUP=root \
OARCONFDIR=$RPM_BUILD_ROOT/%{_sysconfdir} \
OARHOMEDIR=$RPM_BUILD_ROOT/%{_localstatedir}/lib/oar \
OARCONFDIR=$RPM_BUILD_ROOT/%{_sysconfdir} \
PREFIX=$RPM_BUILD_ROOT/usr \
DOCDIR=$RPM_BUILD_ROOT/usr/share/doc/oar-%{version} \
MANDIR=$RPM_BUILD_ROOT/usr/share/man \
OARDIR=$RPM_BUILD_ROOT/%{perl_vendorlib} \
BINDIR=$RPM_BUILD_ROOT/%{_bindir} \
SBINDIR=$RPM_BUILD_ROOT/%{_sbindir} \
WWWDIR=$RPM_BUILD_ROOT/%{wwwdir} \
CGIDIR=$RPM_BUILD_ROOT/var/www/cgi-bin \
BINLINKPATH=%{perl_vendorlib} \
SBINLINKPATH=%{perl_vendorlib} \
doc common configuration server dbinit \
node user draw-gantt desktop-computing-cgi desktop-computing-agent

perl -i -pe 's#^OARDIR=.*#OARDIR=%{perl_vendorlib}/#' $RPM_BUILD_ROOT/%{perl_vendorlib}/sudowrapper.sh
perl -i -pe 's#^(path_cache_directory\s*=\s*).*#$1/%{wwwdir}/DrawGantt/cache#' $RPM_BUILD_ROOT/%{perl_vendorlib}/oar/sudowrapper.sh
perl -i -pe 's#^OARUSER=.*#OARUSER=oar#' $RPM_BUILD_ROOT/%{perl_vendorlib}/sudowrapper.sh
# install oar-server service extra files
cp rpm/oar-server $RPM_BUILD_ROOT/%{_sbindir}/oar-server
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
cp %{SOURCE2} $RPM_BUILD_ROOT/%{_initrddir}/oar-server

perl -i -pe 's#oarstatCmd.*#oarstatCmd=%{perl_vendorlib}/oarstat#' $RPM_BUILD_ROOT/%{_sysconfdir}/DrawGantt.conf
perl -i -pe 's#path_cache_directory.*#path_cache_directory=/var/www/html/DrawGantt/cache/#' $RPM_BUILD_ROOT/%{_sysconfdir}/DrawGantt.conf

mv $RPM_BUILD_ROOT/%{perl_vendorlib}/deploy_nodes.sh $RPM_BUILD_ROOT/%{_sbindir}/deploy_nodes.sh

%clean
rm -rf $RPM_BUILD_ROOT

%pre common
groupadd oar &> /dev/null || true
useradd -d %{_localstatedir}/lib/oar -g oar -p "123456" oar &> /dev/null || true
chown oar.oar %{_localstatedir}/lib/oar -R &> /dev/null
touch /var/log/oar.log && chown oar /var/log/oar.log && chmod 644 /var/log/oar.log || true
if [ ! -e /etc/sudoers ]; then
	echo "Error: No /etc/sudoers file. Is sudo installed ?" 
	exit 1
fi
perl -e '
use Fcntl;
my $sudoers = "/etc/sudoers";
my $sudoerstmp = "/etc/sudoers.tmp";
my $oar_tag="# DO NOT REMOVE, needed by OAR packages";
my $struct=pack("ssll", F_WRLCK, SEEK_CUR, 0, 0);
sysopen (SUDOERS, $sudoers, O_RDWR|O_CREAT, 0440) or die "sysopen $sudoers: $!";
fcntl(SUDOERS, F_SETLK, $struct) or die "fcntl: $!";
sysopen (SUDOERSTMP, "$sudoerstmp", O_RDWR|O_CREAT, 0440) or die "sysopen $sudoerstmp: $!";
print SUDOERSTMP grep (!/$oar_tag/, <SUDOERS>);
print SUDOERSTMP <<EOF;
##BEGIN$oar_tag
apache ALL=(pov) NOPASSWD: ALL
apache ALL= (oar) NOPASSWD: %{perl_vendorlib}/oarstat
apache ALL= (oar) NOPASSWD: %{perl_vendorlib}/oarnodesetting
apache ALL= (oar) NOPASSWD: %{perl_vendorlib}/oarproperty
apache ALL= (oar) NOPASSWD: %{perl_vendorlib}/oarnodes
apache ALL= (root) NOPASSWD: /usr/sbin/arping

Defaults:%oar env_keep="OARDIR PWD"
Defaults:root env_keep="OARDIR PWD"
Cmnd_Alias OARCMD = %{perl_vendorlib}/oarnodes, %{perl_vendorlib}/oarstat, %{perl_vendorlib}/oarsub, %{perl_vendorlib}/oardel, %{perl_vendorlib}/oarhold, %{perl_vendorlib}/oarnotify, %{perl_vendorlib}/oarresume, %{perl_vendorlib}/oar-cgi, %{perl_vendorlib}/oarfetch $oar_tag
ALL ALL=(oar) NOPASSWD: OARCMD $oar_tag
oar ALL=(ALL) NOPASSWD: ALL $oar_tag
##END$oar_tag
EOF
close SUDOERSTMP or die "close $sudoerstmp: $!";
rename "/etc/sudoers.tmp", "/etc/sudoers" or die "rename: $!";
close SUDOERS or die "close $sudoers: $!";
'

%preun common
if [ ! -e /etc/sudoers ]; then
	echo "Error: No /etc/sudoers file. Is sudo installed ?" 
	exit 1
fi
perl -e '
use Fcntl;
my $sudoers = "/etc/sudoers";
my $sudoerstmp = "/etc/sudoers.tmp";
my $oar_tag="# DO NOT REMOVE, needed by OAR package";
my $struct=pack("ssll", F_WRLCK, SEEK_CUR, 0, 0);
sysopen (SUDOERS, $sudoers, O_RDWR|O_CREAT, 0440) or die "sysopen $sudoers: $!";
fcntl(SUDOERS, F_SETLK, $struct) or die "fcntl: $!";
sysopen (SUDOERSTMP, "$sudoerstmp", O_RDWR|O_CREAT, 0440) or die "sysopen $sudoerstmp: $!";
print SUDOERSTMP grep (!/$oar_tag/, <SUDOERS>);
close SUDOERSTMP or die "close $sudoerstmp: $!";
rename "/etc/sudoers.tmp", "/etc/sudoers" or die "rename: $!";
close SUDOERS or die "close $sudoers: $!";
'
userdel oar &> /dev/null || true
groupdel oar &> /dev/null || true
rm -rf /var/log/oar.log || true

%post server
if [ ! -e %{_localstatedir}/lib/oar/.ssh/id_dsa -o \
	! -e %{_localstatedir}/lib/oar/.ssh/id_dsa.pub -o \
	! -e /var/lib/oar/.ssh/authorized_keys ]; then
	mkdir -p %{_localstatedir}/lib/oar/.ssh 
	ssh-keygen -t dsa -q -f %{_localstatedir}/lib/oar/.ssh/id_dsa -N '' || true
	cp %{_localstatedir}/lib/oar/.ssh/id_dsa.pub %{_localstatedir}/lib/oar/.ssh/authorized_keys || true
	chmod 600 %{_localstatedir}/lib/oar/.ssh/authorized_keys
fi
cat <<EOF > %{_localstatedir}/lib/oar/.ssh/config || true
	Host *
	ForwardX11 no
	StrictHostKeyChecking no
EOF
chown oar.oar /var/lib/oar/.ssh -R || true
%_post_service oar-server
echo "- don't forget to create the OAR MySQL database"
echo "%{_sbindir}/oar_db_init" 
echo "- Morever you have to edit and adjust your configuration in %{_sysconfdir}/oar.conf"

%preun server
%_preun_service oar-server

%post draw-gantt
usermod -G "`id -Gn apache | sed 's/ /,/g'`,oar" apache || true
mkdir -p %{wwwdir}/DrawGantt/cache && chown apache.apache %{wwwdir}/DrawGantt/cache || true

%preun draw-gantt
usermod -G "`id -Gn apache | sed 's/oar//;s/^ //;s/ $//;s/ \+/,/g'`" apache || true
rm -rf %{wwwdir}/DrawGantt/cache || true

%post desktop-computing-cgi
usermod -G "`id -Gn apache | sed 's/ /,/g'`,oar" apache || true
ln -sf %{_sbindir}/oarcache %{_sysconfdir}/cron.hourly/oarcache

%preun desktop-computing-cgi
usermod -G "`id -Gn apache | sed 's/oar//;s/^ //;s/ $//;s/ \+/,/g'`" apache || true
rm -f %{_sysconfdir}/cron.hourly/oarcache


%files common
%doc README PACKAGING INSTALL COPYING CHANGELOG AUTHORS
%defattr(-,root,root)
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/oar.conf
%{perl_vendorlib}/sudowrapper.sh
%{perl_vendorlib}/oar_conflib.pm
%{perl_vendorlib}/oar_iolib.pm
%{perl_vendorlib}/oar_Judas.pm
%{perl_vendorlib}/oar_Tools.pm
%attr(755,root,root) %{perl_vendorlib}/bipbip
%{perl_vendorlib}/ping_checker.pm
%attr(755,root,root) %{perl_vendorlib}/oarnodesetting
%attr(755,root,root) %{_bindir}/oarnodesetting
%attr(755,root,root) %{perl_vendorlib}/oarproperty
%attr(755,root,root) %{_bindir}/oarproperty
%{perl_vendorlib}/oarversion.pm
%attr(755,root,root) %{_sysconfdir}/profile.d/oar.sh

%files server
%doc README
%defattr(-,root,root)
%attr(755,root,root) %{_sbindir}/oar-server
%attr(755,root,root) %{_sbindir}/deploy_nodes.sh
%attr(755,root,root) %{_initrddir}/oar-server
%attr(755,root,root) %{_sbindir}/Almighty
%attr(755,root,root) %{_sbindir}/oar_db_init
%attr(755,root,root) %{_bindir}/oarnotify
%attr(755,root,root) %{_sbindir}/oarremovenode
%attr(755,root,root) %{_bindir}/oaraccounting
%{perl_vendorlib}/oar_db_init
%{perl_vendorlib}/oar_jobs.sql
%attr(755,root,root) %{perl_vendorlib}/Leon
%attr(755,root,root) %{perl_vendorlib}/Almighty
%attr(755,root,root) %{perl_vendorlib}/runner
%attr(755,root,root) %{perl_vendorlib}/sarko
%attr(755,root,root) %{perl_vendorlib}/finaud
%{perl_vendorlib}/oar_sched_fifo
%{perl_vendorlib}/Gant.pm
%{perl_vendorlib}/oar_sched_gant
%{perl_vendorlib}/oar_sched_gant_besteffort_deploy_aware
%{perl_vendorlib}/oar_meta_sched
%{perl_vendorlib}/oar_scheduler.pm
%attr(755,root,root) %{perl_vendorlib}/oar_sched_fifo_queue
%attr(755,root,root) %{perl_vendorlib}/oar_sched_fifo_queue_killer
%attr(755,root,root) %{perl_vendorlib}/oarnotify
%attr(755,root,root) %{perl_vendorlib}/NodeChangeState
%{perl_vendorlib}/oar-cgi.pl
%attr(755,root,root) %{perl_vendorlib}/oarremovenode
%attr(755,root,root) %{perl_vendorlib}/oaraccounting

%files user
%doc README
%defattr(-,root,root)
%attr(755,root,root) %{perl_vendorlib}/oarnodes
%attr(755,root,root) %{perl_vendorlib}/oardel
%attr(755,root,root) %{perl_vendorlib}/oarstat
%attr(755,root,root) %{perl_vendorlib}/oarsub
%attr(755,root,root) %{perl_vendorlib}/oarhold
%attr(755,root,root) %{perl_vendorlib}/oarresume
%attr(755,root,root) %{_bindir}/oardel
%attr(755,root,root) %{_bindir}/oarhold
%attr(755,root,root) %{_bindir}/oarnodes
%attr(755,root,root) %{_bindir}/oarsub
%attr(755,root,root) %{_bindir}/oarstat
%attr(755,root,root) %{_bindir}/oarresume
%{_mandir}/man1/oardel.*
%{_mandir}/man1/oarnodes.*
%{_mandir}/man1/oarresume.*
%{_mandir}/man1/oarstat.*
%{_mandir}/man1/oarsub.*
%{_mandir}/man1/oarhold.*

%files node
%doc README
%defattr(-,root,root)
%attr(755,root,root) %{_bindir}/oarexec
%attr(755,root,root) %{_bindir}/oarkill
%attr(755,root,root) %{perl_vendorlib}/oarexec
%attr(755,root,root) %{perl_vendorlib}/oarkill
%attr(755,root,root) %{perl_vendorlib}/oarexecuser.sh
%attr(755,root,root) %{_localstatedir}/lib/oar/oar_prologue
%attr(755,root,root) %{_localstatedir}/lib/oar/oar_epilogue
%attr(755,root,root) %{_localstatedir}/lib/oar/oar_diffuse_script
%attr(755,root,root) %{_localstatedir}/lib/oar/oar_epilogue_local
%attr(755,root,root) %{_localstatedir}/lib/oar/oar_prologue_local
%attr(755,root,root) %{_localstatedir}/lib/oar/lock_user.sh

%files draw-gantt
%doc README
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/DrawGantt.conf
%attr(755,root,root) /var/www/cgi-bin/DrawOARGantt.pl
%attr(755,root,root) %{perl_vendorlib}/oar_sched_gant_g5k
/var/www/cgi-bin/oar_conflib.pm
%{wwwdir}/DrawGantt/Icons/*
%{wwwdir}/DrawGantt/js/*

%files desktop-computing-cgi
%doc README
%defattr(-,root,root)
%attr(755,root,root) %{_sbindir}/oarcache
%attr(755,root,root) %{perl_vendorlib}/oarcache
%attr(755,root,root) %{perl_vendorlib}/oarres
%attr(755,root,root) %{_sbindir}/oarres
%{perl_vendorlib}/oar-cgi
/var/www/cgi-bin/oar-cgi

%files desktop-computing-agent
%doc README
%defattr(-,root,root)
%attr(755,root,root) %{_bindir}/oar-agent

%files doc
%doc README
%defattr(-,root,root)
%doc Docs/desktop-computing.ps
/usr/share/doc/oar-%{version}/html/*
/usr/share/doc/oar-%{version}/Almighty.fig
/usr/share/doc/oar-%{version}/Almighty.ps


