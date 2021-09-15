
# Proyecto de visualizacion de datos con la empresa CEDENAR S.A. E.S.P

Se identifico la necesidad dentro de la empresa de poder visualizar las ubicaciones de diferentes dispositivos que estaba siendo subidos en una base de datos, pero nadie reliazaba un proceso de verificacion en la integridad de esta informacion.

Como alternativo se propuso la creacion de un Dashboard que facilitara la visualizacion en un mapa de estos dispositivos, asi como la posibilidad de actualizar o verificar la informacion de estos mismos.

A continuacion se nombran las librerias principales que fueron usadas para desarollar el prooyecto:

- Dash: Una de las librerias principales de este proyecto. Dash permite la posibilidad de crear dashboards interactivos usando una plantilla escrita en HTLM y CSS, todo desde python. Ademas de eso, dash tiene multiples extensiones desarrolladas por terceros como por ejemplo dash_leaflet.express, la cual nos permite hacer mapas interactivos como si estuvieramos programando en java.
- Pandas: Una de las mejores librerias para el manejo de datos de multiples fuentes.
- Plotly: De los mismos creadores de Dash, plotly nos permite la generacion de diferentes graficos de manera sencilla junto a pandas y Dash.

Para ejecutar el servicio de dash, se abre una terminal desde un ambiente que tenga instaladas todas las librerias necesarias y se ejecuta el siguiente comando:
```Python
python app.py
```
Una vez ejecutado se iniciara un servicio de manera local en esta direccion http://127.0.0.1:8050/. Este tipo de dashboards son faciles de implementar en los servicio de la nube como AWS, es mucho mas recomendable utilizar estos servicios en la nube que adaptar un servidor propio que pueda ejecutar este servicio.

## Resultados

### Mapa interactivo

Este mapa le permite al usuario modificar los valores de un registro que se encuentre subido a la base de datos, tambien le permite al usuario mirar su ubicacion en tiempo real junto con el de los registros, haciendo asi que esta herramienta sea util tanto como para el trabajo en campo como para el trabajo en escritorio para la verificacion de la informacion.

![alt-tex](https://github.com/gabrielcoralc/dash_mapa_cargas_especiales/blob/main/assets/Mapa_interactivo.gif)

### Mapa analisis

El mapa de analisis permite obtener informacion de manera dinamica segun las necesidades del usuario, dandole la posibilidad de seleccionar los registros que este desee desde el mapa y luego presentando la informacion en una grafica de distribucion y en una tabla que puede mostrar las informacion tanto de una manera detallada, como de una manera resumida haciendo agrupaciones de la informacion segun los criterios que el usuario defina, la informacion de esta tabla tambien puede ser descargada como un archivo excel si el usuario asi lo requiere.

![alt-tex](https://github.com/gabrielcoralc/dash_mapa_cargas_especiales/blob/main/assets/Mapa_analisis.gif)


Despues de varias versiones se tiene un producto que cumple con todas las necesidades que presentaba la empresa y incluso surgen nuevas necesidad que se iran supliendo a medida que se vayan implementando nuevas actualizaciones al codigo.

