# SD_Tarea3
Integrantes: Luis Donoso, Mauricio Inostroza

## Ejecución
En el directorio principal ejecutar el comando
```
docker-compose up
```

Para realizar el registro de una receta ejecutar este comando en powershell 
```powershell
$headers = @{}
$headers.Add("Content-Type", "application/json")

$reqUrl = 'http://localhost:3000/create'
$body = '{
"nombre": "Melon",
"apellido": "Musk",
"rut": "1",
"email": "Xmelon_muskX@fruitter.com",
"fecha_nacimiento": "28/06/1971",
"comentario": "Amigdalitis",
"farmacos": "Paracetamol",
"doctor": "El Waton de la Fruta"
}'

$response = Invoke-RestMethod -Uri $reqUrl -Method Post -Headers $headers -ContentType 'application/json' -Body $body
$response | ConvertTo-Json
```
o realizar una request tipo POST con un body Json a través de Postman
```
url: http://localhost:3000/create
```
```
{
    "nombre": "Melon",
    "apellido": "Musk",
    "rut": "1",
    "email": "Xmelon_muskX@fruitter.com",
    "fecha_nacimiento": "28/06/1971",
    "comentario": "Amigdalitis",
    "farmacos": "Paracetamol",
    "doctor": "El Waton de la Fruta"
}
```
También se puede modificar una receta, ejecutando el siguiente comando
```powershell
$headers = @{}
$headers.Add("Content-Type", "application/json")

$reqUrl = 'http://localhost:3000/edit'
$body = '{
    "id": 1,
    "comentario": "Amigdalitis aguda",
    "farmacos": "Paracetamol con aguita",
    "doctor": "El Waton de la Fruta"
}'

$response = Invoke-RestMethod -Uri $reqUrl -Method Post -Headers $headers -ContentType 'application/json' -Body $body
$response | ConvertTo-Json
```
o realizar una request tipo POST con un body Json a través de Postman
```
url: http://localhost:3000/edit
```
```
{
    "id": 1,
    "comentario": "Amigdalitis aguda",
    "farmacos": "Paracetamol con aguita",
    "doctor": "El Waton de la Fruta"
}
```
Finalmente se puede eliminar una receta, para esto se ejecuta lo siguiente
```powershell
$headers = @{}
$headers.Add("Content-Type", "application/json")

$reqUrl = 'http://localhost:3000/delete'
$body = '{
    "id": 1
}'

$response = Invoke-RestMethod -Uri $reqUrl -Method Post -Headers $headers -ContentType 'application/json' -Body $body
$response | ConvertTo-Json
```
```
o realizar una request tipo POST con un body Json a través de Postman
```
url: http://localhost:3000/delete
```
```
{
    "id": 1
}
```

##1. Explique la arquitectura que Cassandra maneja. Cuando se crea el clúster ¿Cómo los nodos se conectan? ¿Qué ocurre cuando un cliente realiza una petición a uno de los nodos? ¿Qué ocurre cuando uno de los nodos se desconecta? ¿La red generada entre los nodos siempre es eficiente? ¿Existe balanceo de carga?
##2. Cassandra posee principalmente dos estrategias para mantener redundancia en la replicación de datos. ¿Cuáles son estos? ¿Cuál es la ventaja de uno sobre otro? ¿Cuál utilizaría usted para en el caso actual y por qué? Justifique apropiadamente su respuesta.
##3. Teniendo en cuenta el contexto del problema ¿Usted cree que la solución propuesta es la correcta? ¿Qué ocurre cuando se quiere escalar en la solución? ¿Qué mejoras implementaría? Oriente su respuesta hacia el Sharding (la replicación/distribución de los datos) y comente una estrategia que podría seguir para ordenar los datos.