<?php
session_start();
$dsn = "pgsql:host=localhost;port=5432;dbname=arm_user;";
$user = "mct";
$password = "00123";

try {
    $pdo = new PDO($dsn, $user, $password, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

    if ($_SERVER["REQUEST_METHOD"] == "POST") {
        $username = trim($_POST["username"]);
        $password = $_POST["password"];

        echo "<h3>🔍 Debug Mode（登入不會跳轉）</h3>";

        echo "<p>🔹 **輸入的帳號:** <strong>$username</strong></p>";
        echo "<p>🔹 **輸入的密碼:** <strong>$password</strong></p>";

        // 查詢使用者帳號
        $stmt = $pdo->prepare("SELECT * FROM staff WHERE staff_name = :username");
        $stmt->execute(['username' => $username]);
        $user = $stmt->fetch(PDO::FETCH_ASSOC);

        echo "<h3>🔹 **從資料庫查詢的結果:**</h3>";
        var_dump($user); // 顯示查詢結果

        if ($user) {
            echo "<h3>🔹 **密碼驗證結果:**</h3>";
            $verify = password_verify($password, $user['password_hash']);
            var_dump($verify); // 顯示 true 或 false

            if ($verify) {
                $_SESSION['user'] = $user['staff_name'];
                var_dump($_SESSION);
                echo "<p style='color: green;'>✅ **密碼驗證成功！Session 設定完成！**</p>";
                //header("Location: page1.php");
            } else {
                echo "<p style='color: red;'>❌ **密碼驗證失敗！密碼不匹配！**</p>";
            }
        } else {
            echo "<p style='color: red;'>❌ **找不到該帳號！**</p>";
        }
    }
} catch (PDOException $e) {
    die("資料庫錯誤：" . $e->getMessage());
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>登入測試 - Debug Mode</title>
</head>
<body>
    <h2>請登入</h2>
    <form method="post">
        帳號: <input type="text" name="username" required><br>
        密碼: <input type="password" name="password" required><br>
        <button type="submit">登入</button>
    </form>
</body>
</html>
