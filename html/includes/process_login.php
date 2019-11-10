<?php
include_once 'db_connect.php';
include_once 'functions.php';

// ziggy_session_start(); // Our custom secure way of starting a PHP session.

?>
<html>
    <body>
        Welcome <?php echo $_POST["email"]; ?>
    </body>
</html>

