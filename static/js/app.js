document.getElementById('uploadForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    const xhr = new XMLHttpRequest();

    xhr.open('POST', form.action, true);

    xhr.upload.addEventListener('progress', function (event) {
        if (event.lengthComputable) {
            const percent = (event.loaded / event.total) * 100;
            const progressBar = document.getElementById('progressBar');
            document.getElementById('progressContainer').style.display = 'block';
            progressBar.value = percent;
        }
    });

    xhr.addEventListener('load', function () {
        if (xhr.status === 200) {
            alert('File uploaded successfully!');
            window.location.reload();
        } else {
            alert('Error uploading file!');
        }
    });

    xhr.send(formData);
});
