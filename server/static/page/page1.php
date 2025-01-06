<?php
session_start();

if (!isset($_SESSION['username'])) {
    header("Location: ../../index.php");
    exit();
}
?>
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="icon" href="../photo/index.ico" type="image/x-icon"/>
        <title>機械手臂倉儲系統 - 監控系統</title>
    </head>
    <body>
        <?php echo "<h1>歡迎，" . $_SESSION['username'] . "！</h1>"; ?>
        <a href='logout.php'>登出</a>
    </body>
</html>
