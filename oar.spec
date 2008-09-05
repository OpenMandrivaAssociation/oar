%define version 2.3.1
%define release %mkrel 6
%define wwwdir /var/www/html
	
Name:		oar
Version:	%{version}
Release:	%{release}
Summary:	OAR Batch Scheduler
License:	GPL
Group:		System/Servers
Url:		http://oar.imag.fr
Source0:	https://gforge.inria.fr/frs/download.php/5170/%{name}-%{version}.tar.gz
Source1:	oar-server.init
Source2:	oar-node.init
Source3:	oar-server.sysconfig
Source4:	oar-node.sysconfig
Patch1: 	oar-2.3.1-fix-install.patch
Patch2: 	oar-2.3.1-fix-documentation-build.patch
Patch3: 	oar-2.3.1-monika-no-private-library.patch
Patch4: 	oar-2.3.1-monika-fhs.patch
Patch5: 	oar-2.3.1-fix-pod.patch
Patch6: 	oar-2.3.1-fix-database-creation.patch
BuildRequires:	python-docutils
BuildRoot:	%{_tmppath}/%{name}-%{version}

%description 
This is OAR Batch Scheduler

%package common
Summary:	OAR batch scheduler common package
Group:		System/Servers
BuildArch: 	noarch
Requires:	openssh-clients
Requires:	openssh-server

%description common
This package installs the server part or the OAR batch scheduler

%package server
Summary:	OAR batch scheduler server package
Group:		System/Servers
Requires:	oar-common = %version-%release
Requires:	fping
Requires:	nmap

%description server
This package installs the server part or the OAR batch scheduler

%package admin
Summary:	OAR batch scheduler administration tools package
Group:		System/Servers
Requires:	oar-common = %version-%release
requires:   ruby-dbi

%description admin
This package installs some useful tools to help the administrator of a oar
server (resources manipulation, admission rules edition, ...)

%package user
Summary:	OAR batch scheduler node package
Group:		System/Servers
Requires:	oar-common = %version-%release
Requires:	perl(YAML)
BuildArch: 	noarch

%description user
This package install the submition and query part or the OAR batch scheduler

%package node
Summary:	OAR batch scheduler node package
Group:		System/Servers
Requires:	oar-common = %version-%release

%description node
This package installs the execution node part or the OAR batch scheduler

%package web-status
Summary:	OAR batch scheduler web-status package
Group:		System/Servers
Requires:	oar-common = %version-%release
Requires:	oar-user = %version-%release
requires:   apache
requires:   ruby-gd
requires:   ruby-dbi

%description web-status
This package installs the OAR batch scheduler Gantt reservation diagram CGI:
DrawGantt and the instant cluster state visualization CGI: Monika

%package doc
Summary:	OAR batch scheduler documentation package
Group:		Books/Computer books

%description doc
This package install some documentation for OAR batch scheduler

%prep
%setup -q
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1
%patch5 -p1
%patch6 -p1

%build
cd Docs/documentation
%make

%install
%__rm -rf %{buildroot}

%__make common configuration libs doc-install server dbinit node user draw-gantt monika www-conf tools \
    OARUSER=oar \
    PREFIX=%{_prefix} \
    OARCONFDIR=%{_sysconfdir}/%{name} \
    OARDIR=%{_datadir}/%{name} \
    DOCDIR=%{_docdir}/%{name} \
    MANDIR=%{_mandir} \
    WWWDIR=/var/www/%{name} \
    CGIDIR=/var/www/%{name} \
    DESTDIR=%{buildroot}

perl -pi -e 's|/usr/lib/oar|%{_datadir}/%{name}|'  \
    %{buildroot}%{_docdir}/%{name}/html/OAR-DOCUMENTATION-ADMIN.html \
    %{buildroot}%{_datadir}/%{name}/oarnodesetting_ssh \
    %{buildroot}%{_sysconfdir}/%{name}/oar.conf

perl -pi \
    -e 's|^#OAR_RUNTIME_DIRECTORY=.*|OAR_RUNTIME_DIRECTORY="/var/lib/oar"|;' \
    -e 's|^#OPENSSH_CMD=.*|OPENSSH_CMD="/usr/bin/ssh -p 6667"|;' \
     %{buildroot}%{_sysconfdir}/%{name}/oar.conf

# apache configuration
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
Alias /monika %{_var}/www/%{name}/monika
Alias /drawgantt %{_var}/www/%{name}/drawgantt

<Directory %{_var}/www/%{name}/monika>
    Options ExecCGI
    DirectoryIndex monika.cgi
    Allow from all
</Directory>

<Directory %{_var}/www/%{name}/drawgantt>
    Options ExecCGI FollowSymlinks
    DirectoryIndex drawgantt.cgi
    Allow from all
</Directory>
EOF

rm -f %{buildroot}%{_sysconfdir}/%{name}/apache.conf
install -d -m 755 %{buildroot}%{_var}/www/%{name}/drawgantt
install -d -m 755 %{buildroot}%{_var}/lib/%{name}/drawgantt
install -d -m 755 %{buildroot}%{_var}/www/%{name}/monika
pushd %{buildroot}%{_var}/www/%{name}
mv drawgantt.cgi drawgantt
mv monika.cgi monika
mv userInfos.cgi monika
mv monika.css monika
pushd drawgantt
rmdir cache
ln -sf ../../../lib/%{name}/drawgantt cache
popd
popd

perl -pi -e 's|^web_root.*|web_root: "%{_var}/www/%{name}"|' \
    %{buildroot}%{_sysconfdir}/%{name}/drawgantt.conf
perl -pi -e 's|^css_path.*|css_path = /monika/monika.css|' \
    %{buildroot}%{_sysconfdir}/%{name}/monika.conf

chmod 640  %{buildroot}%{_sysconfdir}/%{name}/monika.conf
chmod 640  %{buildroot}%{_sysconfdir}/%{name}/drawgantt.conf

install -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name}.conf <<EOF
/var/log/oar.log {
    daily
    missingok
    notifempty
}
EOF

install -d -m 755 %{buildroot}%{_sysconfdir}/cron.d
cat > %{buildroot}%{_sysconfdir}/cron.d/%{name}-server <<EOF
0 * * * * root /usr/share/oar/oaraccounting
}
EOF
cat > %{buildroot}%{_sysconfdir}/cron.d/%{name}-node <<EOF
0 * * * * root /usr/share/oar/oarnodecheckrun
}
EOF

install -d -m 755 %{buildroot}%{_initrddir}
install -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/oar-server
install -m 755 %{SOURCE2} %{buildroot}%{_initrddir}/oar-node
install -d -m 755 %{buildroot}%{_sysconfdir}/sysconfig
install -m 755 %{SOURCE3} %{buildroot}%{_sysconfdir}/sysconfig/oar-server
install -m 755 %{SOURCE4} %{buildroot}%{_sysconfdir}/sysconfig/oar-node

cat > %{buildroot}%{_sbindir}/oar-server <<'EOF'
#!/bin/sh

%{_sbindir}/Almighty $* &
jobs -p  > /var/run/`basename $0`.pid
EOF
chmod +x %{buildroot}%{_sbindir}/oar-server

install -d -m 755 %{buildroot}%{_var}/lib/oar
install -d -m 755 %{buildroot}%{_var}/lib/oar/.ssh
install -d -m 755 %{buildroot}%{_var}/lib/oar/checklogs
cat > %{buildroot}%{_var}/lib/oar/.ssh/config <<EOF
	Host *
	ForwardX11 no
	StrictHostKeyChecking no
EOF

cat > README.urpmi <<EOF
Post-installation instructions

You have to create a database for the server, using either:
- postgresql: install perl-DBD-pg, and run oar_psql_db_init
- mysql: install perl-DBD-mysql, and run oar_mysql_db_init
EOF

%clean
rm -rf %{buildroot}

%pre common
%_pre_useradd %{name} %{_var}/lib/%{name} %{_datadir}/%{name}/oarsh_shell
%create_ghostfile /var/log/oar.log oar oar 644

%postun common
%_postun_userdel %{name}

%post server
if [ $1 = 1 ]; then
    cd %{_var}/lib/%{name}/.ssh
    if [ ! -e id_dsa.pub -o ! -e id_dsa.pub -o ! -e authorized_keys ]; then
        ssh-keygen -t dsa -q -f id_dsa -N ''
        cp id_dsa.pub authorized_keys
        chown oar.oar id_dsa id_dsa.pub authorized_keys
    fi
    cd -
fi
%_post_service oar-server

%preun server
%_preun_service oar-server

%post node
# create oar sshd keys
if [ ! -f %{_sysconfdir}/%{name}/oar_ssh_host_rsa_key ]; then
    rm -f %{_sysconfdir}/%{name}/oar_ssh_host_rsa_key.pub
    cp %{_sysconfdir}/ssh/ssh_host_rsa_key \
        %{_sysconfdir}/%{name}/oar_ssh_host_rsa_key
    cp %{_sysconfdir}/ssh/ssh_host_rsa_key.pub \
        %{_sysconfdir}/%{name}/oar_ssh_host_rsa_key.pub
fi

if [ ! -f %{_sysconfdir}/%{name}/oar_ssh_host_dsa_key ]; then
    rm -f %{_sysconfdir}/%{name}/oar_ssh_host_dsa_key.pub
    cp %{_sysconfdir}/ssh/ssh_host_dsa_key \
        %{_sysconfdir}/%{name}/oar_ssh_host_dsa_key
    cp %{_sysconfdir}/ssh/ssh_host_dsa_key.pub \
        %{_sysconfdir}/%{name}/oar_ssh_host_dsa_key.pub
fi

%_post_service oar-node

%preun node
%_preun_service oar-node

%post web-status
%_post_webapp

%preun web-status
%_postun_webapp

%files common
%defattr(-,root,root)
%config(noreplace) %{_sysconfdir}/%{name}/oar.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}.conf
%attr(6750,oar,oar) %{_sbindir}/oarnodesetting
%{_bindir}/oarcp
%{_bindir}/oarsh
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/oardodo
%{_datadir}/%{name}/oar_Judas.pm
%{_datadir}/%{name}/oar_Tools.pm
%{_datadir}/%{name}/oar_conflib.pm
%{_datadir}/%{name}/oar_iolib.pm
%{_datadir}/%{name}/oar_resource_tree.pm
%attr(6750,root,oar) %{_datadir}/%{name}/oardodo/oardodo
%{_datadir}/%{name}/oarnodesetting
%{_datadir}/%{name}/oarnodesetting_ssh
%{_datadir}/%{name}/oarsh
%attr(6755,oar,oar) %{_datadir}/%{name}/oarsh_oardo
%{_datadir}/%{name}/oarversion.pm
%{_datadir}/%{name}/sentinelle.pl
%{_datadir}/%{name}/oarsh_shell
%{_mandir}/man1/oarcp.1*
%{_mandir}/man1/oarsh.1*
%{_mandir}/man1/oarnodesetting.1*
%dir %attr(-,oar,oar) %{_var}/lib/oar

%files server
%doc README README.urpmi
%defattr(-,root,root)
%config(noreplace) %{_initrddir}/oar-server
%config(noreplace) %{_sysconfdir}/sysconfig/oar-server
%config(noreplace) %{_sysconfdir}/cron.d/oar-server
%config(noreplace) %{_sysconfdir}/%{name}/job_resource_manager.pl
%config(noreplace) %{_sysconfdir}/%{name}/oarmonitor_sensor.pl
%config(noreplace) %{_sysconfdir}/%{name}/server_epilogue
%config(noreplace) %{_sysconfdir}/%{name}/server_prologue
%config(noreplace) %{_sysconfdir}/%{name}/suspend_resume_manager.pl
%attr(-,oar,oar) %dir %{_var}/lib/%{name}/.ssh
%attr(-,oar,oar) %config(noreplace) %{_var}/lib/%{name}/.ssh/config
%attr(6750,oar,oar) %{_sbindir}/Almighty
%{_sbindir}/oar-server
%attr(6750,oar,oar) %{_sbindir}/oar_mysql_db_init
%{_sbindir}/oar_psql_db_init
%attr(6750,oar,oar) %{_sbindir}/oaraccounting
%attr(6750,oar,oar) %{_sbindir}/oarmonitor
%attr(6750,oar,oar) %{_sbindir}/oarnotify
%attr(6750,oar,oar) %{_sbindir}/oarproperty
%attr(6750,oar,oar) %{_sbindir}/oarremoveresource
%{_mandir}/man1/Almighty.1*
%{_mandir}/man1/oar_mysql_db_init.1*
%{_mandir}/man1/oaraccounting.1*
%{_mandir}/man1/oarmonitor.1*
%{_mandir}/man1/oarnotify.1*
%{_mandir}/man1/oarproperty.1*
%{_mandir}/man1/oarremoveresource.1*
%{_datadir}/%{name}/Almighty
%{_datadir}/%{name}/Gantt_hole_storage.pm
%{_datadir}/%{name}/Leon
%{_datadir}/%{name}/NodeChangeState
%{_datadir}/%{name}/bipbip
%{_datadir}/%{name}/default_data.sql
%{_datadir}/%{name}/finaud
%{_datadir}/%{name}/mysql_default_admission_rules.sql
%{_datadir}/%{name}/mysql_structure.sql
%{_datadir}/%{name}/oar_meta_sched
%{_datadir}/%{name}/oar_mysql_db_init
%{_datadir}/%{name}/oar_psql_db_init
%{_datadir}/%{name}/oar_scheduler.pm
%{_datadir}/%{name}/oaraccounting
%{_datadir}/%{name}/oarexec
%{_datadir}/%{name}/oarmonitor
%{_datadir}/%{name}/oarnotify
%{_datadir}/%{name}/oarproperty
%{_datadir}/%{name}/oarremoveresource
%{_datadir}/%{name}/pg_default_admission_rules.sql
%{_datadir}/%{name}/pg_structure.sql
%{_datadir}/%{name}/ping_checker.pm
%{_datadir}/%{name}/runner
%{_datadir}/%{name}/sarko
%{_datadir}/%{name}/schedulers/oar_sched_gantt_with_timesharing
%{_datadir}/%{name}/schedulers/oar_sched_gantt_with_timesharing_and_fairsharing

%files user
%defattr(-,root,root)
%{_datadir}/%{name}/oarnodes
%{_datadir}/%{name}/oardel
%{_datadir}/%{name}/oarstat
%{_datadir}/%{name}/oarsub
%{_datadir}/%{name}/oarhold
%{_datadir}/%{name}/oarresume
%attr(6755,oar,oar) %{_bindir}/oardel
%attr(6755,oar,oar) %{_bindir}/oarhold
%attr(6755,oar,oar) %{_bindir}/oarnodes
%attr(6755,oar,oar) %{_bindir}/oarresume
%attr(6755,oar,oar) %{_bindir}/oarstat
%attr(6755,oar,oar) %{_bindir}/oarsub
%{_bindir}/oarmonitor_graph_gen
%{_mandir}/man1/oardel.1*
%{_mandir}/man1/oarhold.1*
%{_mandir}/man1/oarmonitor_graph_gen.1*
%{_mandir}/man1/oarnodes.*
%{_mandir}/man1/oarresume.*
%{_mandir}/man1/oarstat.*
%{_mandir}/man1/oarsub.*

%files node
%defattr(-,root,root)
%config(noreplace) %{_initrddir}/oar-node
%config(noreplace) %{_sysconfdir}/sysconfig/oar-node
%config(noreplace) %{_sysconfdir}/cron.d/oar-node
%config(noreplace) %{_sysconfdir}/oar/check.d
%config(noreplace) %{_sysconfdir}/oar/epilogue
%config(noreplace) %{_sysconfdir}/oar/prologue
%config(noreplace) %{_sysconfdir}/oar/sshd_config
%{_bindir}/oarnodechecklist
%{_bindir}/oarnodecheckquery
%{_datadir}/%{name}/detect_resources
%{_datadir}/%{name}/oarnodecheckrun
%dir %attr(-,oar,oar) %{_var}/lib/oar/checklogs

%files web-status
%defattr(-,root,root)
%config(noreplace) %{_webappconfdir}/%{name}.conf
%attr(-,root,apache) %config(noreplace) %{_sysconfdir}/oar/drawgantt.conf
%attr(-,root,apache) %config(noreplace) %{_sysconfdir}/oar/monika.conf
%{_datadir}/%{name}/monika
%{_var}/www/%{name}
%attr(-,apache,apache) %{_var}/lib/%{name}/drawgantt

%files doc
%defattr(-,root,root)
%{_docdir}/%{name}

%files admin
%defattr(-,root,root)
%{_datadir}/%{name}/oar_modules.rb
%{_datadir}/%{name}/oaradmin.rb
%{_datadir}/%{name}/oaradmin_modules.rb
%attr(6750,oar,oar) %{_sbindir}/oaradmin
%{_mandir}/man1/oaradmin.1*
