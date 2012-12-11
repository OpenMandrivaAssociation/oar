%define version 2.4.3
%define release %mkrel 1
	
Name:		oar
Version:	%{version}
Release:	%{release}
Summary:	OAR Batch Scheduler
License:	GPL
Group:		System/Servers
Url:		http://oar.imag.fr
Source0:	https://gforge.inria.fr/frs/download.php/24906/%{name}-%version.tar.bz2
Source1:	oar-server.init
Source2:	oar-node.init
Source3:	oar-server.sysconfig
Source4:	oar-node.sysconfig
Patch0:		oar-2.4.4-drawgantt.php.patch
#Patch4: 	oar-2.4.1-monika-fhs.patch
BuildRequires:	python-docutils
BuildArch: 	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}

%description 
This is OAR Batch Scheduler

%package common
Summary:	OAR batch scheduler common package
Group:		System/Servers
Requires:	openssh-clients
Requires:	openssh-server
Requires:	perl-Sys-Hostname-Long perl-Time-HiRes perl-IPC-SysV perl-Getopt-Long
Requires:	perl-IO-Socket-INET6 perl-Time-Local perl-Data-Dumper perl-Storable
Requires:	perl-File-Temp

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
%if %mdkversion < 201010
Requires(post):   rpm-helper
Requires(postun):   rpm-helper
%endif

%description web-status
This package installs the OAR batch scheduler Gantt reservation diagram CGI:
DrawGantt and the instant cluster state visualization CGI: Monika

%package api
Summary:	OAR batch scheduler API
Group:		System/Servers
requires:	oar-user

%description api
You may test the API with a simple wget:
wget -O - http://localhost:/oarapi/resources.html
It should give you the list of resources in the yaml format
but enclosed in an html page. To test if the authentication works,
you need to post a new job. See the example.txt file that gives you
example queries with a ruby rest client.

%package doc
Summary:	OAR batch scheduler documentation package
Group:		Books/Computer books

%description doc
This package install some documentation for OAR batch scheduler

%prep
%setup -q
%patch0 -p0

%build
# Modify Makefile for chown commands to be non-fatal as the permissions
# are set by the packaging
perl -i -pe "s/chown/-chown/" Makefile
perl -i -pe "s/-o root//" Makefile
perl -i -pe "s/-g root//" Makefile

cd Docs/documentation
%make

%install
%__rm -rf %{buildroot}

%__make common configuration libs doc-install server dbinit node user draw-gantt monika www-conf tools api \
    OARUSER=oar \
    PREFIX=%{_prefix} \
    OARCONFDIR=%{_sysconfdir}/%{name} \
    OARDIR=%{_datadir}/%{name} \
    DOCDIR=%{_docdir}/%{name} \
    MANDIR=%{_mandir} \
    WWWDIR=/var/www/%{name} \
    CGIDIR=/var/www/%{name} \
    PERLLIBDIR=%perl_sitelib \
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
install -d -m 755 %{buildroot}%{webappconfdir}
cat > %{buildroot}%{webappconfdir}/%{name}.conf <<EOF
Alias /monika %{_var}/www/%{name}/monika
Alias /drawgantt %{_var}/www/%{name}/drawgantt
Alias /oarapi %{_var}/www/%{name}/oarapi

<Directory %{_var}/www/%{name}/monika>
    Options ExecCGI
    DirectoryIndex monika.cgi
    Order allow,deny
    Allow from all
</Directory>

<Directory %{_var}/www/%{name}/drawgantt>
    Options ExecCGI FollowSymlinks
    DirectoryIndex drawgantt.cgi
    Order allow,deny
    Allow from all
</Directory>

<Directory %{_var}/www/%{name}/oarapi>
    Options ExecCGI FollowSymlinks
    DirectoryIndex oarapi.cgi
    Order allow,deny
    Allow from all
</Directory>
EOF

install -d -m 755 %{buildroot}%{_var}/www/%{name}/drawgantt
cat > %{buildroot}%{_var}/www/%{name}/drawgantt/.htaccess<<EOF
<Files "config.php">
Order Allow,Deny
Deny from All
</Files>
EOF

cat > %{buildroot}%{_var}/www/%{name}/drawgantt/config.php<<EOF
<?php
$dbhost   = '127.0.0.1' ;
$dbname   = 'oar'   ;
$dbuser   = 'oar' ;
$dbpass = 'oar' ;
?>
EOF

rm -f %{buildroot}%{_sysconfdir}/%{name}/apache.conf
install -d -m 755 %{buildroot}%{_var}/lib/%{name}/drawgantt
install -d -m 755 %{buildroot}%{_var}/www/%{name}/monika
install -m 755 VisualizationInterfaces/DrawGantt/drawgantt.cgi %{buildroot}%{_var}/www/%{name}/drawgantt
cp -av VisualizationInterfaces/DrawGantt/drawgantt.php %{buildroot}%{_var}/www/%{name}/drawgantt
cp -av VisualizationInterfaces/DrawGantt/Icons %{buildroot}%{_var}/www/%{name}/drawgantt
cp -av VisualizationInterfaces/DrawGantt/js %{buildroot}%{_var}/www/%{name}/drawgantt
cp -av VisualizationInterfaces/Monika/*.cgi %{buildroot}%{_var}/www/%{name}/monika
cp -av VisualizationInterfaces/Monika/monika.css %{buildroot}%{_var}/www/%{name}/monika
# remove unwated files
rm -vf %{buildroot}%{_var}/www/%{name}/monika.*
rm -vf %{buildroot}%{_var}/www/%{name}/drawgantt.*
pushd %{buildroot}%{_var}/lib/%{name}/drawgantt
#rmdir cache
ln -sf ../../../lib/%{name}/drawgantt cache
popd

perl -pi -e 's|^web_root.*|web_root: "%{_var}/www/%{name}"|' \
    %{buildroot}%{_sysconfdir}/%{name}/drawgantt.conf
perl -pi -e 's|^css_path.*|css_path = /monika/monika.css|' \
    %{buildroot}%{_sysconfdir}/%{name}/monika.conf

chmod 640  %{buildroot}%{_sysconfdir}/%{name}/monika.conf
chmod 640  %{buildroot}%{_sysconfdir}/%{name}/drawgantt.conf

install -d -m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cp -av rpm/SOURCES/oar-common.logrotate %{buildroot}%{_sysconfdir}/logrotate.d/%{name}.conf

install -d -m 755 %{buildroot}%{_sysconfdir}/cron.d
cp -av rpm/SOURCES/oar-server.cron.d %{buildroot}%{_sysconfdir}/cron.d/%{name}-server
cp -av rpm/SOURCES/oar-node.cron.d %{buildroot}%{_sysconfdir}/cron.d/%{name}-node

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
    PasswordAuthentication no
    AddressFamily inet
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
%if %mdkversion < 201010
%_post_webapp
%endif

%preun web-status
%if %mdkversion < 201010
%_postun_webapp
%endif

%files common
%doc COPYING CHANGELOG AUTHORS TODO README
%defattr(-,root,root)
%config(noreplace) %attr(640,oar,root) %{_sysconfdir}/%{name}/oar.conf
%config(noreplace) %{_sysconfdir}/%{name}/oarnodesetting_ssh
%config(noreplace) %{_sysconfdir}/%{name}/update_cpuset_id.sh

%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}.conf
%attr(6750,oar,oar) %{_sbindir}/oarnodesetting
%{_bindir}/oarcp
%{_bindir}/oarsh
%{_bindir}/oarprint
%dir %{_datadir}/%{name}
%dir %attr(755,root,oar) %{_datadir}/%{name}/oardodo
%{_datadir}/%{name}/oar_Judas.pm
%{_datadir}/%{name}/oar_Tools.pm
%{_datadir}/%{name}/oar_conflib.pm
%{_datadir}/%{name}/oar_iolib.pm
%{_datadir}/%{name}/oar_resource_tree.pm
%attr(6750,root,oar) %{_datadir}/%{name}/oardodo/oardodo
%{_datadir}/%{name}/oarnodesetting
%{_datadir}/%{name}/oarsh
%attr(6755,oar,oar) %{_datadir}/%{name}/oarsh_oardo
%{_datadir}/%{name}/oarversion.pm
%{_datadir}/%{name}/sentinelle.pl
%{_datadir}/%{name}/oarsh_shell
%{_mandir}/man1/oarcp.1*
%{_mandir}/man1/oarsh.1*
%{_mandir}/man1/oarprint.1*
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
%{_sysconfdir}/%{name}/shut_down_nodes.sh
%{_sysconfdir}/%{name}/wake_up_nodes.sh
%config(noreplace) %{_sysconfdir}/%{name}/suspend_resume_manager.pl
%attr(-,oar,oar) %dir %{_var}/lib/%{name}/.ssh
%attr(-,oar,oar) %config(noreplace) %{_var}/lib/%{name}/.ssh/config
%attr(6750,oar,oar) %{_sbindir}/Almighty
%{_sbindir}/oar-server
%attr(6750,oar,oar) %{_sbindir}/oar_mysql_db_init
%attr(6750,oar,oar) %{_sbindir}/oar_resources_init
%{_sbindir}/oar_psql_db_init
%attr(6750,oar,oar) %{_sbindir}/oar_checkdb
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
%{_datadir}/%{name}/db_upgrade
%{_datadir}/%{name}/oar_checkdb.pl
%{_datadir}/%{name}/oarnodes.v2_3
%{_datadir}/%{name}/oarnodes_lib.pm
%{_datadir}/%{name}/oarstat.v2_3
%{_datadir}/%{name}/oarstat_lib.pm
%{_datadir}/%{name}/oarsub_lib.pm
%{_datadir}/%{name}/oar_Hulot.pm
%{_datadir}/%{name}/window_forker.pm

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
%attr(6755,oar,oar) %{_bindir}/oarnodes.old
%attr(6755,oar,oar) %{_bindir}/oarresume
%attr(6755,oar,oar) %{_bindir}/oarstat
%attr(6755,oar,oar) %{_bindir}/oarstat.old
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
#%{_datadir}/%{name}/monika
%{perl_sitelib}/monika
%{_var}/www/%{name}
%attr(-,apache,apache) %{_var}/lib/%{name}/drawgantt
%attr(-,apache,apache) %{_var}/lib/drawgantt-files

%files api
%doc API/INSTALL API/oarapi_example*
%{_sysconfdir}/%{name}/apache-api.conf
%{_sysconfdir}/%{name}/api_html_header.pl
%{_sysconfdir}/%{name}/api_html_postform.pl
%{_datadir}/%{name}/oar_apilib.pm
%{_datadir}/%{name}/oarapi.pl

%files doc
%doc FAQ-ADMIN FAQ-USER GUIDELINES QUICK* CPUSET
%defattr(-,root,root)
%{_docdir}/%{name}

%files admin
%defattr(-,root,root)
%{_datadir}/%{name}/oar_modules.rb
%{_datadir}/%{name}/oaradmin.rb
%{_datadir}/%{name}/oaradmin_modules.rb
%attr(6750,oar,oar) %{_sbindir}/oaradmin
%{_mandir}/man1/oaradmin.1*




%changelog
* Fri Dec 03 2010 Antoine Ginies <aginies@mandriva.com> 2.4.3-1mdv2011.0
+ Revision: 606110
- add missing perl* requires, add OAR batch scheduler API, use included logrotate and crond files, update oar/.ssh/config file, fix oar.conf permission, fix oardodo permission, add new oar_Hulot.pm and window_forker.pm module,
- oar-2.4.3, fix initscripts (use oar_checkdb), add a drawgantt configuration file

* Fri Feb 26 2010 Guillaume Rousse <guillomovitch@mandriva.org> 2.4.1-1mdv2010.1
+ Revision: 511883
- new version

* Mon Feb 08 2010 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.5-3mdv2010.1
+ Revision: 502437
- rely on filetrigger for reloading apache configuration begining with 2010.1, rpm-helper macros otherwise

* Wed Jan 27 2010 Antoine Ginies <aginies@mandriva.com> 2.3.5-2mdv2010.1
+ Revision: 497296
- bump the release to re-submit to the cluster (build loop on klodia...)

* Wed Jan 27 2010 Antoine Ginies <aginies@mandriva.com> 2.3.5-1mdv2010.1
+ Revision: 497222
- upload new tarball
- release 2.3.5

* Sat Jun 27 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.4-1mdv2010.0
+ Revision: 390069
- new version

* Sat Mar 14 2009 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.3-2mdv2009.1
+ Revision: 355068
- all packages are noarch

* Sun Dec 21 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.3-1mdv2009.1
+ Revision: 317122
- new version
- rediff patch 1
- drop patches 2, 3, 5 and 6 (merged upstream)

* Fri Sep 05 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.1-6mdv2009.0
+ Revision: 281226
- fix executables perms and ownership
- fix drawgantt apache configuration
- fix man pages syntax
- fix mysql database creation on utf-8 systems

* Thu Sep 04 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.1-4mdv2009.0
+ Revision: 280458
- better installation patch
- add dependencies on ruby-dbi, now it is available

* Thu Aug 14 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.1-3mdv2009.0
+ Revision: 272094
- various fixes for web package

* Thu Aug 14 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.1-2mdv2009.0
+ Revision: 272026
- add ruby-gd dependency for web package
- drop mysql-specific dependencies, as postgresl is also supported, and update post-install instructions
- fix main directory location in various places
- fix server wrapper perms
- fix occurence of buildroot in installed files
- fix webapps configuration files

* Wed Aug 13 2008 Guillaume Rousse <guillomovitch@mandriva.org> 2.3.1-1mdv2009.0
+ Revision: 271476
- new version
  large spec cleanup, based on upstream one
- use README.urpmi instead of stdout to display post-installations instructions
- use standard rpm-helper macros for servicce
- don't requires a local mysql server
- spec cleanup: drop implicit dependencies

* Wed Jul 30 2008 Thierry Vignaud <tv@mandriva.org> 1.6.2-14mdv2009.0
+ Revision: 254156
- rebuild

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Fri Dec 21 2007 Olivier Blin <oblin@mandriva.com> 1.6.2-12mdv2008.1
+ Revision: 136633
- restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request
    - fix man pages


* Wed Mar 07 2007 Nicolas Lécureuil <neoclust@mandriva.org> 1.6.2-12mdv2007.1
+ Revision: 134808
- Fix Group

* Fri Mar 02 2007 Antoine Ginies <aginies@mandriva.com> 1.6.2-11mdv2007.1
+ Revision: 131349
- remove the -o user -g group in Makefile
- Import oar

* Wed Nov 08 2006 Antoine Ginies <aginies@mandriva.com> 1.6.2-11mdviggi
- Add nmap requires

* Fri Nov 03 2006 Antoine Ginies <aginies@mandriva.com> 1.6.2-10mdviggi
- Change DrawOARGantt cache directory

* Fri Oct 27 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-9mdviggi
- add an fping require

* Tue Oct 24 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-8mdviggi
- fix again cache directory

* Wed Oct 18 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-7mdviggi
- fix cache directory of DrawOARGantt
- move deploy_node.sh in /usr/sbin
- adjust oar-server output

* Sun Oct 15 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-6mdviggi
- laucnh Almighty with oar-server script

* Sun Oct 15 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-5mdviggi
- fix perm on authorized_keys

* Sat Oct 14 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-4mdviggi
- fix initscript (no simple way to use daemon)

* Sat Oct 14 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-3mdviggi
- fix oarstatcmd in DrawGantt conf
- fix apache sudoers conf
- fix all user OARcmd access
- fix OARUSER in sudowrapper.sh script

* Fri Oct 13 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-2mdviggi
- use oar.sh in /etc/profile.d 
- fix problem in sudoers OARDIR env

* Tue Oct 10 2006 iggi <iggi@guibux.mandrakesoft.com> 1.6.2-1mdviggi
- release rc2

* Thu Mar 02 2006 Antoine Ginies <aginies@mandriva.com> 1.6.1-1mdk
- based on Pierre Neyron spec
- fix requires
- fix oar-server service
- fix use /usr/lib/perl5/vendor_perl/5.8.8 to fix various pb with @INC (oar doesn't use MakeMaker...)
- move oar.conf to common
- fix DrawGant cache directory
- fix DrawGantt path
- fix defattr
- fix various chmod
- fix OARDIR in sudowrapper.sh script

* Wed May 11 2005 Pierre Lombard <pl@icatis.com> 1.6-1
- New upstream version.

* Fri Feb 04 2005 Sebastien Georget <sebastien.georget@sophia.inria.fr> 1.4-1
- Update dependencies, change Source0 and %%setup to use default oar distribution

* Thu Jul 01 2004 Pierre Neyron <pierre.neyron@imag.fr> 1.0-1
- First RPM package

