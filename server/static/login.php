<?php
session_start();
$dsn = "pgsql:host=localhost;port=5432;dbname=arm;";
$user = "mct";
$password = "00123";

try {
    $pdo = new PDO($dsn, $user, $password, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        $username = trim($_POST["username"]);
        $password = $_POST["password"];

        // 查詢使用者帳號
        $stmt = $pdo->prepare("SELECT * FROM staff WHERE staff_name = :username");
        $stmt->execute(['username' => $username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($user) {
            $verify = password_verify($password, $user['password_hash']);
            if ($verify) {
                $_SESSION['username'] = $user['staff_name']; // 設定 Session
                header("Location: main.php"); // 登入成功導向首頁
                exit;
            } else {
                exit;
            }
        } else {
            header("Location: logout.php");
            exit;
        }
    }
} catch (PDOException $e) {
    die("資料庫錯誤：" . $e->getMessage());
}
?>
