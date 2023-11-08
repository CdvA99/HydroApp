# Librerías
from flask import Flask, render_template, request, redirect, flash,url_for,send_file,Response
from openpyxl import Workbook
from io import BytesIO
from flask_login import LoginManager, login_user, UserMixin, login_required, current_user, logout_user
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
import os
import serial
from io import BytesIO



app = Flask(__name__, template_folder='template')
app.secret_key = "HydroAceroS.A.S" 

# Configuración de Login
login_manager = LoginManager()
login_manager.login_view = "login"  # Ruta a la que se redirigirá si un usuario no está autenticado
login_manager.init_app(app)

# Conexion a la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'inventario_hya'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# Definición de rutas

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin')
@login_required 
def admin():
    return render_template('administrador/admin.html')

@app.route('/usuario')
@login_required  # Protege esta ruta para que solo los usuarios autenticados (usuario) puedan acceder
def usuario():
    return render_template('usuario/usuario.html')

# Clase User para manejar usuarios
class User(UserMixin):
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role

    @staticmethod
    def get(user_id):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
        account = cur.fetchone()
        cur.close()
        if account:
            return User(user_id, account['usuario'], account['id_rol'])
        return None

# Configuración del user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

#-------- LOGIN----------------------
@app.route('/acceso-login', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        _usuario = request.form['txtUsuario']
        _password = request.form['txtPassword']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM usuarios WHERE usuario = %s AND password = %s', (_usuario, _password,))
        account = cur.fetchone()

        if account:
            user_id = account['id']
            role = account['id_rol']

            user = User(user_id, _usuario, role)  

            login_user(user)  

            if role == 1:
                return redirect('/admin')
            elif role == 2:
                return redirect('/usuario')
        else:
            flash("Usuario o contraseña incorrectos", 'error')

    return render_template('index.html',mensaje="Usuario O Contraseña Incorrectas")

# Ruta para cerrar la sesión
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado la sesión', 'success')
    return redirect('/')
#--------------------------------------------------------------------------------------
#-------CRUD DE USUARIOS------------------------
#------------------------------------------------
# Ruta para ver la lista de usuarios
@app.route('/listar_usuarios')
def listar_usuarios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, usuario, password, id_rol FROM usuarios")
    usuarios = cur.fetchall()
    cur.close()
    return render_template('administrador/listar_usuarios.html', usuarios=usuarios)

# Ruta para agregar un usuario

@app.route('/agregar_usuario', methods=["POST"])
def agregar_usuario():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        id_rol = request.form['id_rol']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (usuario, password, id_rol) VALUES (%s, %s, %s)", (usuario, password, id_rol))
        mysql.connection.commit()
        cur.close()
        
        flash('Usuario agregado con éxito', 'success')
        return redirect('/listar_usuarios')

# Ruta para editar un usuario
@app.route('/editar_usuario/<int:id>', methods=["POST"])
def editar_usuario(id):
    if request.method == 'POST':
        nuevo_usuario = request.form['nuevo_usuario']
        nuevo_password = request.form['nuevo_password']
        nuevo_id_rol = request.form['nuevo_id_rol']

        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET usuario = %s, password = %s, id_rol = %s WHERE id = %s", (nuevo_usuario, nuevo_password, nuevo_id_rol, id))
        mysql.connection.commit()
        cur.close()
        
        flash('Usuario actualizado con éxito', 'success')
        return redirect('/listar_usuarios')

# Ruta para eliminar un usuario
@app.route('/eliminar_usuario/<int:id>')
def eliminar_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Usuario eliminado con éxito', 'success')
    return redirect('/listar_usuarios')

#--------------------------------------------

#--------------------------------------------------------------------------------------
#-------CRUD DE PRODUCTOS------------------------
#------------------------------------------------


#-----LISTAR PRODUCTOS-------------
#-----Cargar productos para usuario administrador-------------
@app.route('/productosA', methods= ["GET", "POST"])
def productosA(): 
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM productos")
    productos = cur.fetchall()
    cur.close()
    
    return render_template("administrador/productosA.html",productos=productos)

#-----Cargar productos para usuario estandar-------------
@app.route('/productosB', methods= ["GET", "POST"])
def productosB(): 
    cur = mysql.connection.cursor()
    cur.execute("SELECT  id,descripcion,precio_venta,cantidad,foto,ubicacion,id_categoria FROM productos")
    productos = cur.fetchall()
    cur.close()
    
    return render_template("usuario/productosB.html",productos=productos)
#----------------------------------


# Ruta para agregar un producto
@app.route('/agregar_producto', methods=["POST"])
def agregar_producto():
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        precio_costo = request.form['precio_costo']
        precio_venta = request.form['precio_venta']
        cantidad = request.form['cantidad']
        foto = request.files['foto']
        ubicacion = request.form['ubicacion']
        id_categoria = request.form['id_categoria']

        if foto:
            if not os.path.exists('uploads'):
                os.mkdir('uploads')

            filename = secure_filename(foto.filename)
            ruta_imagen = os.path.join('uploads', filename)
            foto.save(ruta_imagen)

            with open(ruta_imagen, 'rb') as f:
                imagen_bytes = f.read()

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO productos (descripcion, precio_costo, precio_venta, cantidad, foto, ubicacion, id_categoria) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (descripcion, precio_costo, precio_venta, cantidad, imagen_bytes, ubicacion, id_categoria))
            mysql.connection.commit()
            cur.close()

            flash('Producto agregado con éxito', 'success')
            return redirect(url_for('productosA'))
        
     
    


       
 
 #----------------------------------
# Mostrar imagen
 
@app.route('/mostrar_imagen/<int:imagen_id>')
def mostrar_imagen(imagen_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT foto FROM productos WHERE id = %s", (imagen_id,))
    imagen_data = cur.fetchone()
    cur.close()

    if imagen_data:
     return Response(imagen_data['foto'], content_type="image/jpeg")

    return 'Imagen no encontrada', 404   
    
# Ruta para editar un producto
@app.route('/editar_producto/<int:id>', methods=["POST", "GET"])
def editar_producto(id):
    if request.method == 'POST':
        nuevo_foto = request.files['nuevo_foto']
        nuevo_descripcion = request.form['nuevo_descripcion']
        nuevo_precio_costo = request.form['nuevo_precio_costo']
        nuevo_precio_venta = request.form['nuevo_precio_venta']
        nuevo_cantidad = request.form['nuevo_cantidad']
        nuevo_ubicacion = request.form['nuevo_ubicacion']
        nuevo_id_categoria = request.form['nuevo_id_categoria']

        # Actualizar la imagen si se proporciona una nueva
        if nuevo_foto:
            if not os.path.exists('uploads'):
                os.mkdir('uploads')

            filename = secure_filename(f"{id}_{nuevo_foto.filename}")
            ruta_imagen = os.path.join('uploads', filename)
            nuevo_foto.save(ruta_imagen)

            with open(ruta_imagen, 'rb') as f:
                imagen_bytes = f.read()

            # Actualizar la imagen en la base de datos
            cur = mysql.connection.cursor()
            cur.execute("UPDATE productos SET foto = %s WHERE id = %s", (imagen_bytes, id))
            mysql.connection.commit()
            cur.close()
            flash('Imagen actualizada con éxito', 'success')

        # Actualizar otros campos en la base de datos
        cur = mysql.connection.cursor()
        cur.execute("UPDATE productos SET descripcion = %s, precio_costo = %s, precio_venta = %s, cantidad = %s, ubicacion = %s, id_categoria = %s WHERE id = %s",
                    (nuevo_descripcion, nuevo_precio_costo, nuevo_precio_venta, nuevo_cantidad, nuevo_ubicacion, nuevo_id_categoria, id))
        mysql.connection.commit()
        cur.close()
        flash('Producto actualizado con éxito', 'success')

        return redirect('/productosA')

    else:
        # Si es una solicitud GET, debes recuperar los datos del producto
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM productos WHERE id = %s", (id,))
        producto = cur.fetchone()
        cur.close()

        if producto:
            return render_template('editar_producto.html', producto=producto)
        else:
            flash('Producto no encontrado', 'error')
            return redirect('/productosA')


# Ruta para eliminar un producto
@app.route('/eliminar_producto/<int:id>')
def eliminar_producto(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM productos WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    
    flash('Producto eliminado con éxito', 'success')
    return redirect('/productosA')


# Ruta para buscar productos para administradores
@app.route('/buscar_productos', methods=['POST'])
def buscar_productos():
    if request.method == 'POST':
        # Obtener el término de búsqueda del formulario
        termino_busqueda = request.form['termino_busqueda']

        # Realizar una consulta a la base de datos para buscar productos que coincidan con el término
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM productos WHERE descripcion LIKE %s", ('%' + termino_busqueda + '%',))
        productos = cur.fetchall()
        cur.close()

        # Renderizar la plantilla con los resultados de la búsqueda
        return render_template('administrador/productosA.html', productos=productos)
    
# Ruta para buscar productos para usuario estandar
@app.route('/buscar_productosB', methods=['POST'])
def buscar_productosB():
    if request.method == 'POST':
        # Obtener el término de búsqueda del formulario
        termino_busqueda = request.form['termino_busqueda']

        # Realizar una consulta a la base de datos para buscar productos que coincidan con el término
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM productos WHERE descripcion LIKE %s", ('%' + termino_busqueda + '%',))
        productos = cur.fetchall()
        cur.close()

        # Renderizar la plantilla con los resultados de la búsqueda
        return render_template('usuario/productosB.html', productos=productos)

#--------------------------------------------------------------------------------------
#-------EXPORTAR LISTA DE PRODUCTOS EN EXCEL------------------------
#------------------------------------------------
def obtener_productos_desde_db():
    cur = mysql.connection.cursor()
    cur.execute("SELECT productos.id, productos.descripcion, productos.precio_costo, productos.precio_venta,productos.cantidad,categoria.categoria FROM productos INNER JOIN categoria ON productos.id_categoria = categoria.id")
    productos = cur.fetchall()
    cur.close()
    return productos

@app.route('/descargar_productos', methods=['GET'])
def descargar_productos():
    # Obtener los datos de las transacciones (de tu base de datos)
    productos = obtener_productos_desde_db()

    # Crear un libro de trabajo de Excel
    wb = Workbook()
    ws = wb.active

    # Escribir los encabezados
    ws.append(["ID", "Producto", "Precio Costo", "Precio Venta", "Cantidad", "Categoria"])

    # Escribir los datos de las transacciones
    for producto in productos:
        ws.append([producto['id'], producto['descripcion'], producto['precio_costo'], producto['precio_venta'], producto['cantidad'], producto['categoria']])

    # Guardar el archivo Excel en memoria
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Devolver el archivo Excel como una respuesta para descargar
    return send_file(output, as_attachment=True, download_name='Listado de productos.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


#--------------------------------------------------------------------------------------
#-------TRANSACCIONES------------------------
#------------------------------------------------
# Ruta para mostrar y registrar transacciones para administradores
@app.route('/transacciones', methods=['GET', 'POST'])
def transacciones():
    if request.method == 'POST':
        producto_id = request.form['producto_id']
        tipo = request.form['tipo']
        cantidad = int(request.form['cantidad'])
        observaciones = request.form['observaciones']

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO transacciones (producto_id, tipo, cantidad,observaciones) VALUES (%s, %s, %s,%s)", (producto_id, tipo, cantidad,observaciones))

        if tipo == 'Entrada':
            cur.execute("UPDATE productos SET cantidad = cantidad + %s WHERE id = %s", (cantidad, producto_id))
        else:
            cur.execute("UPDATE productos SET cantidad = cantidad - %s WHERE id = %s", (cantidad, producto_id))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('transacciones'))

    # Obtener la lista de productos para mostrar en el formulario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, descripcion FROM productos")
    productos = cur.fetchall()
    cur.close()

    # Obtener la lista de transacciones para mostrar en la tabla
    cur = mysql.connection.cursor()
    cur.execute("SELECT transacciones.id, productos.descripcion, transacciones.tipo, transacciones.observaciones,transacciones.cantidad,transacciones.fecha FROM transacciones INNER JOIN productos ON transacciones.producto_id = productos.id")
    transacciones = cur.fetchall()
    cur.close()

    return render_template('administrador/transacciones.html', productos=productos, transacciones=transacciones)

#--------------------------------------------------------------------------------------
#-------TRANSACCIONES PARA ROL USUARIO------------------------
#------------------------------------------------
# Ruta para mostrar y registrar transacciones para usuarios
@app.route('/transaccionesB', methods=['GET', 'POST'])
def transaccionesB():
    if request.method == 'POST':
        producto_id = request.form['producto_id']
        tipo = request.form['tipo']
        cantidad = int(request.form['cantidad'])
        observaciones = request.form['observaciones']

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO transacciones (producto_id, tipo, cantidad,observaciones) VALUES (%s, %s, %s,%s)", (producto_id, tipo, cantidad,observaciones))

        if tipo == 'Entrada':
            cur.execute("UPDATE productos SET cantidad = cantidad + %s WHERE id = %s", (cantidad, producto_id))
        else:
            cur.execute("UPDATE productos SET cantidad = cantidad - %s WHERE id = %s", (cantidad, producto_id))

        mysql.connection.commit()
        cur.close()

        return redirect(url_for('transaccionesB'))

    # Obtener la lista de productos para mostrar en el formulario
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, descripcion FROM productos")
    productos = cur.fetchall()
    cur.close()

    # Obtener la lista de transacciones para mostrar en la tabla
    cur = mysql.connection.cursor()
    cur.execute("SELECT transacciones.id, productos.descripcion, transacciones.tipo, transacciones.observaciones,transacciones.cantidad,transacciones.fecha FROM transacciones INNER JOIN productos ON transacciones.producto_id = productos.id")
    transacciones = cur.fetchall()
    cur.close()

    return render_template('usuario/transaccionesB.html', productos=productos, transacciones=transacciones)


#--------------------------------------------------------------------------------------
#-------EXPORTAR LISTA DE TRANSACCIONES EN EXCEL------------------------
#------------------------------------------------
def obtener_transacciones_desde_db():
    cur = mysql.connection.cursor()
    cur.execute("SELECT transacciones.id, productos.descripcion, transacciones.tipo, transacciones.observaciones,transacciones.cantidad,transacciones.fecha FROM transacciones INNER JOIN productos ON transacciones.producto_id = productos.id")
    transacciones = cur.fetchall()
    cur.close()
    return transacciones

@app.route('/descargar_excel', methods=['GET'])
def descargar_excel():
    # Obtener los datos de las transacciones (de tu base de datos)
    transacciones = obtener_transacciones_desde_db()

    # Crear un libro de trabajo de Excel
    wb = Workbook()
    ws = wb.active

    # Escribir los encabezados
    ws.append(["ID", "Producto", "Tipo de Transacción", "Cantidad", "Observaciones", "Fecha"])

    # Escribir los datos de las transacciones
    for transaccion in transacciones:
        ws.append([transaccion['id'], transaccion['descripcion'], transaccion['tipo'], transaccion['cantidad'], transaccion['observaciones'], transaccion['fecha']])

    # Guardar el archivo Excel en memoria
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # Devolver el archivo Excel como una respuesta para descargar
    return send_file(output, as_attachment=True, download_name='transacciones.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')








if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5000)
