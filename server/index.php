<?php
session_start();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
	<link rel="icon" href="./static/index.ico" type="image/x-icon"/>
    <title>Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC&display=swap');
        * {
            margin: 0;
            padding: 0;
            list-style: none;
        }
        html, body {
            height: 100%;
            font-family: 'Noto Sans TC', sans-serif;
        }
        body {
            background-image: url('./static/login.jpg');
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
                const url = new URL(window.location.href);
                url.searchParams.delete('logout');
                window.history.replaceState({}, document.title, url.toString());
            }
        };
    </script>
</head>
<body>
    <div class="login">
        <form class="form" action="./static/login.php" method="POST">
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
