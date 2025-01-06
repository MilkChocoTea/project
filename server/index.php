<?php
session_start();
if (isset($_GET['logout']) && $_GET['logout'] == 1) {
    $logoutMessage = "您因為10分鐘沒有任何動作，而被系統自動登出。";
} else {
    $logoutMessage = null;
}
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    // 設定資料庫連線資訊
    $host = "localhost";
    $dbname = "arm_user";
    $dbuser = "mct";
    $dbpassword = "00123";
    $conn = pg_connect("host=$host dbname=$dbname user=$dbuser password=$dbpassword");
    if (!$conn) {
        die("資料庫連線失敗");
    }
    $inputUsername = $_POST['username'];
    $inputPassword = $_POST['password'];
    $query = "SELECT * FROM user_ip WHERE user_id = $1";
    $result = pg_query_params($conn, $query, array($inputUsername));

    if (!$result) {
        die("查詢失敗：" . pg_last_error($conn));
    }
    if ($row = pg_fetch_assoc($result)) {
        if ($inputPassword === $row['user_pw']) {
            $_SESSION['username'] = $row['user_id'];
            header("Location: ./static/page/page1.php");
            exit();
        } else {
            echo "密碼錯誤";
        }
    } else {
        echo "用戶名不存在";
    }
    pg_close($conn);
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
	<link rel="icon" href=".\static\photo/index.ico" type="image/x-icon"/>
    <title>Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            list-style: none;
        }
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC&display=swap');

        html, body {
            height: 100%;
            font-family: 'Noto Sans TC', sans-serif;
        }
        body {
            background-image: url('./static/photo/login.jpg');
            background-repeat: no-repeat;
            background-size: cover;
            display: flex;
        }
        .login {
            width: 600px;
            height: 450px;
            margin: auto;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            border: 10px solid #fff;
            box-shadow: 0 0 45px #000;
            backdrop-filter: blur(5px);
            display: flex;
        }
        .form {
            width: 400px;
            height: 75%;
            margin: auto;
            color: #fff;
        }
        .form h1 {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #fff;
        }
        .form label {
            line-height: 2;
        }
        .form input {
            width: 95%;
            font-size: 20px;
            border: 1px solid #aaa;
            line-height: 2;
            border-radius: 5px;
            padding-left: 10px;
        }
        .form .login_btn {
            width: 90%;
            margin-top: 50px;
            font-style: 0;
        }
        .form button {
            font-size: 20px;
            font-weight: bold;
            border-radius: 5px;
            border: none;
            background-color: #EAEAEA;
            width: 45%;
            height: 45px;
            font-family: 'Noto Sans TC', sans-serif;
        }
    </style>
    <script>
        window.onload = function() {
            const message = "<?php echo $logoutMessage; ?>";
            if (message) {
                alert(message);
            }
        };
    </script>
</head>
<body>
    <div class="login">
        <form class="form" action="index.php" method="POST">
            <h1>Login</h1>
            <div class="login_id">
                <label for="username">User Name</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="login_pw">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <div class="login_btn">
                <button type="submit">Login</button>
            </div>
        </form>
    </div>
</body>
</html>
