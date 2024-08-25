<?php
    $validUsers = [
        'username' => 'password',
    ];

    function Authenticate($username, $password)
    {
        global $validUsers;
        return isset($validUsers[$username]) && $validUsers[$username] === $password;
    }

    function GenerateUniqueFilename($directory, $filename)
    {
        $fileExtension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
        $fileBaseName = pathinfo($filename, PATHINFO_FILENAME);
        $newFilename = $filename;
        $counter = 1;

        while (file_exists($directory . DIRECTORY_SEPARATOR . $newFilename))
        {
            $newFilename = $fileBaseName . '_' . $counter . '.' . $fileExtension;
            $counter++;
        }

        return $newFilename;
    }

    function HandleFileUpload()
    {
        $allowedExtensions = ['jpeg', 'jpg', 'png', 'gif', 'txt', 'wav'];
        $maxFileSize = 20 * 1024 * 1024;
        $targetDir = __DIR__ . DIRECTORY_SEPARATOR . "Uploads";
    
        if (!file_exists($targetDir))
            mkdir($targetDir, 0311, true);
    
        foreach ($_FILES as $file)
        {
            $fileExtension = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
            $fileSize = $file['size'];
    
            if (!in_array($fileExtension, $allowedExtensions))
            {
                echo "File type not allowed: " . htmlspecialchars($file['name']) . "<br>";
                continue;
            }
    
            if ($fileSize > $maxFileSize)
            {
                echo "File size exceeds the maximum limit of 20MB: " . htmlspecialchars($file['name']) . "<br>";
                continue;
            }
    
            $finfo = new finfo(FILEINFO_MIME_TYPE);
            $mimeType = $finfo->file($file['tmp_name']);
            if (strpos($mimeType, 'application/x-executable') !== false || strpos($mimeType, 'application/x-msdownload') !== false)
            {
                echo "Executable files are not allowed: " . htmlspecialchars($file['name']) . "<br>";
                continue;
            }
    
            $uniqueFilename = GenerateUniqueFilename($targetDir, $file['name']);
            $targetFile = $targetDir . DIRECTORY_SEPARATOR . $uniqueFilename;
    
            if (move_uploaded_file($file['tmp_name'], $targetFile))
            {
                chmod($targetFile, 0200);
                echo "The file " . htmlspecialchars($uniqueFilename) . " has been uploaded.<br>";
            }
            else
                echo "Sorry, there was an error uploading your file: " . htmlspecialchars($file['name']) . "<br>";
        }
    }

    $RootPath = ".";
    $Title = "VirtualSelf";
    $Description = "Anti-Theft / Remote Access Utility";
    include "$RootPath/Modules/StandardLibrary.php";
?>

<html>
    <head>
        <?php PrintHead($RootPath, $Title, $Description, "$RootPath/Pictures/VirtualSelf.png"); ?>
    </head>

    <body>
        <div class="Main">
            <div class="Content">
                <?php PrintTitleBar($RootPath); ?>

                <center>
                    <h1><?php echo $Title;?></h1>
                    <p><small><?php echo $Description;?></small></p>

                    <img src="<?php echo $RootPath; ?>/Pictures/VirtualSelf.png" width=250px><br><br>

                    <?php
                        if ($_SERVER['REQUEST_METHOD'] === 'POST')
                        {
                            if (isset($_POST['username']) && isset($_POST['password']))
                            {
                                $username = $_POST['username'];
                                $password = $_POST['password'];

                                if (Authenticate($username, $password))
                                    HandleFileUpload();
                                else
                                    echo "Authentication failed. Invalid username or password.";
                            }
                            else
                                echo "Username and password are required.";
                        }
                        else
                            echo "Invalid request method.";
                    ?>
                <br> <br>
                </center>

                <hr>
                <?php PrintFooter($RootPath); ?>
            </div>
        </div>
    </body>
</html>
