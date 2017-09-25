2. Edit the ``/etc/shadowfiend/shadowfiend.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://shadowfiend:SHADOWFIEND_DBPASS@controller/shadowfiend
