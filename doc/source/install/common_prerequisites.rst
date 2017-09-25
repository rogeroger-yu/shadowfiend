Prerequisites
-------------

Before you install and configure the shadowfiend service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p

   * Create the ``shadowfiend`` database:

     .. code-block:: none

        CREATE DATABASE shadowfiend;

   * Grant proper access to the ``shadowfiend`` database:

     .. code-block:: none

        GRANT ALL PRIVILEGES ON shadowfiend.* TO 'shadowfiend'@'localhost' \
          IDENTIFIED BY 'SHADOWFIEND_DBPASS';
        GRANT ALL PRIVILEGES ON shadowfiend.* TO 'shadowfiend'@'%' \
          IDENTIFIED BY 'SHADOWFIEND_DBPASS';

     Replace ``SHADOWFIEND_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: none

        exit;

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``shadowfiend`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt shadowfiend

   * Add the ``admin`` role to the ``shadowfiend`` user:

     .. code-block:: console

        $ openstack role add --project service --user shadowfiend admin

   * Create the shadowfiend service entities:

     .. code-block:: console

        $ openstack service create --name shadowfiend --description "shadowfiend" shadowfiend

#. Create the shadowfiend service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        shadowfiend public http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        shadowfiend internal http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        shadowfiend admin http://controller:XXXX/vY/%\(tenant_id\)s
