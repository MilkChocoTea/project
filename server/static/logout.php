<?php
session_start();
if (isset($_GET['logout']) && $_GET['logout'] == 1) {
    header("Location: ../index.php?logout=1");
} else {
    header("Location: ../index.php");
    session_destroy();
}
exit();
?>