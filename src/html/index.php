<!DOCTYPE html>
<html>
<head>
  <title>Hostname en Nginx+PHP</title>
</head>
<body>
  <h1>
    <?php
      $customMessage = getenv('CUSTOM_MESSAGE') ?: '¡Bienvenido!';
      echo $customMessage;
    ?>
  </h1>
  <h2>
    <?php
            $entorno = getenv('APP_ENV') ?: 'entorno desconocido';
      echo "Estas en el entorno <strong>$entorno</strong>";
    ?>
  </h2>
  <p>El hostname de este contenedor es: <strong><?php echo gethostname(); ?></strong></p>
</body>
</html>
