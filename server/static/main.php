<?php
session_start();
ini_set('session.gc_maxlifetime', 600);
session_set_cookie_params(600);
if (!isset($_SESSION['username'])) {
    header("Location: logout.php");
    exit();
}
$pages = [
    ['label' => '機台們','src' => 'machine.php'],
    ['label' => '貨物們','src' => 'item.php'],
    ['label' => '人們','src' => 'staff.php']
];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="index.ico" type="image/x-icon"/>
    <title>機械手臂倉儲系統 - 監控系統</title>
    <script src="script.js" defer></script>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="side">
        <div class="wellcome"><?php echo "<h1>User：" . $_SESSION['username'] . "</h1>"; ?></div>
        <div class="side-page">
            <?php foreach ($pages as $page) : ?>
                <button class="btn" onclick="showpages('<?php echo $page['src']; ?>')"><?php echo $page['label']; ?></button>
            <?php endforeach; ?>
        </div>
        <div class="logout"><a href='logout.php'>Logout</a></div>
    </div>
    <div class="list" id="content"></div>
</body>
</html>
