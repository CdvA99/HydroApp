 // Controlador de eventos para el botón "Seleccionar Carpeta de Destino"
 document.getElementById('selectFolder').addEventListener('click', function () {
    // Abre el explorador de archivos para seleccionar una carpeta
    document.getElementById('folderInput').click();
});

// Controlador de eventos para el botón "Exportar a Excel"
document.getElementById('exportToExcel').addEventListener('click', function () {
    // Realizar una solicitud al servidor para exportar a Excel
    fetch('/exportar_excel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(transacciones) // Puedes enviar datos adicionales si es necesario
    })
    .then(response => response.blob())
    .then(blob => {
        // Crear un objeto de flujo de bytes desde el blob
        const blobUrl = window.URL.createObjectURL(blob);

        // Crear un enlace oculto
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = blobUrl;
        a.download = 'transacciones.xlsx';

        // Disparar un clic en el enlace para iniciar la descarga
        a.click();

        // Revocar la URL del blob después de la descarga
        window.URL.revokeObjectURL(blobUrl);
    });
});