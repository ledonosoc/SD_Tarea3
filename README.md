# SD_Tarea3
Integrantes: Luis Donoso, Mauricio Inostroza

## Ejecución
En el directorio principal ejecutar el comando
```
docker-compose up
```

Para crear el entorno de trabajo se debe acceder a la dirección principal de la api, la cual se encarga de crear los keyspace con su respectivo factor de replicación con las tablas "paciente" y "recetas" en su interior.
```
'http://localhost:3000/'
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

o realizar una request tipo POST con un body Json a través de Postman
```
url: http://localhost:3000/delete
```
```
{
    "id": 1
}
```

## 1. Explique la arquitectura que Cassandra maneja.
* **Cuando se crea el clúster ¿Cómo los nodos se conectan?** 
Cuando más de un nodo es agregado a un cluster, los nodos se conectan entre ellos, dado a que Cassandra utiliza un arquitectura peer-to-peer (P2P), por lo que cada nodo realiza operaciones de base de datos y puede recibir y completar consultas de clientes sin necesidad de un nodo maestro. 
* **¿Qué ocurre cuando un cliente realiza una petición a uno de los nodos?**
El nodo que recibe la petición se considera como el nodo coordinador, este nodo procede a enviar la petición a los nodos replica determinado por el nivel de consistencia especificada por el cliente. El coodinador envia una petición que permite saber si los nodos réplica que los nodos esten actualizados, finalmente la información con la marca de tiempo más actualizada es envíada al cliente.
* **¿Qué ocurre cuando uno de los nodos se desconecta?**
Cassandra utiliza un método de detección de fallas, determinado localmente por el *gossip state* e historial, si un nodo se ha desconectado o se ha vuelto a conectar. Esta información es utilizada para evitar que una petición de cliente tenga un ruteo que los dirija a nodos que no están disponibles. Este detector de fallas determina cuando ocurre la desconección y marca el nodo como desconectado. Cassandra asume que el nodo volverá a conectarse eventualmente y que los cambios permanentes dentro del cluster son ejecutados exclusivamente usando **nodetool**.
* **¿La red generada entre los nodos siempre es eficiente?**
Como todos los nodos se conectan entre sí cuando se establece conexión y se realiza constante intercambio de mensajes para verificar la presencia de los nodos, a medida que aumenta la cantidad de nodos esto puede generar un consumo excesivo del ancho de banda disponible ya que todos los nodos deben reportarse de manera constante.
* **¿Existe balanceo de carga?**
Existen distintas politicas de balanceo de carga que pueden ser definidas mediante la importación de la librería cassandra.policies entre las cuales se pueden mencionar: RoundRobinPolicy que es la seleccionada por defecto y distribuye las querys entre todos los nodos del clúster indenpendiente del datacenter al cual este pertenezca, además de DCAwareRoundRobinPolicy, TokenAwarePolicy, WhiteListRoundRobinPolicy, HostFilterPolicy las cuales definen un distinto comportamiento según la seleción.
## 2. Cassandra posee principalmente dos estrategias para mantener redundancia en la replicación de datos. ¿Cuáles son estos? ¿Cuál es la ventaja de uno sobre otro? ¿Cuál utilizaría usted para en el caso actual y por qué? Justifique apropiadamente su respuesta.
Las dos estrategias para mantener la redundancia en la replicación de datos corresponden a "SimpleStrategy" y "NetworkTopologyStrategy". La ventaja de usar "SimpleStrategy" es que tiene mayor facilidad de implementación ya que requiere unicamente definir la cantidad de replicas de la información. Por otro lado la ventaja de utilizar "NetworkTopologyStrategy" es que se tiene una mayor organización de los datos, ya que estos son guardados especificamente en los datacenters que se asignes, permitiendo una mejor distribución de los recursos. Como en este caso se trata de una base de datos pequeña y que posee una cantidad reducida de nodos, es suficiente con aplicar "SimpleStrategy" para que funcione de manera correcta.
## 3. Teniendo en cuenta el contexto del problema ¿Usted cree que la solución propuesta es la correcta? ¿Qué ocurre cuando se quiere escalar en la solución? ¿Qué mejoras implementaría? Oriente su respuesta hacia el Sharding (la replicación/distribución de los datos) y comente una estrategia que podría seguir para ordenar los datos.
Como se mencionó anteriormente como se trata de un problema de pequeña escala la solución propuesta con "SimpleStrategy" permite la funcionalidad del sistema de manera correcta. En caso de requerir escalar esta solución y añadir mas nodos, sería conveniente definir nuevos datacenters con el fin de balancear la carga de la información entre los distintos nodos y generar mayor disponibilidad de las replicas al distribuirlas de manera más eficiente implementando la estrategia "NetworkTopologyStrategy". 
