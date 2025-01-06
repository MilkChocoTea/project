<?php
session_start();

if (!isset($_SESSION['username'])) {
    header("Location: ../../index.php");
    exit();
}

echo "<h1>歡迎，" . $_SESSION['username'] . "！</h1>";
echo "<a href='logout.php'>登出</a>";
?>