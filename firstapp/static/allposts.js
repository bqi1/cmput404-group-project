function getFileData() {
    return new Promise((resolve, reject) => {
        imageFile = document.getElementById("image_file").files;

        var fileReader = new FileReader();
        if (fileReader && imageFile && imageFile.length) {
            fileReader.readAsDataURL(imageFile[0]);
            fileReader.onload = function () {
                resolve(fileReader.result);
            };
        }
        else {
            imageUrl = document.getElementById("image_link").value;
            if (imageUrl == "") { resolve('0'); }
            else { resolve(imageUrl); }
        }


    });

}

function resetLink() {
    imageUrl = document.getElementById("image_link");
    imageUrl.value = ""; 
}

function resetFile() {
    imageFile = document.getElementById("image_file");
    imageFile.value = "";
}

function makePost() {
    title = document.getElementById("title").value;
    desc = document.getElementById("desc").value;
    markdown = +document.getElementById("md").checked;
    content = document.getElementById("content").value;
    var image = 0;

    console.log(document.getElementById("image_file").files);
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;


    // Cannot accept empty values

    if (title == "" || desc == "" || content == "") {
        alert("Please fill out all of the fields.");
        return 1;
    }

    // This code came from https://stackoverflow.com/questions/22680695/how-to-get-byte-array-from-input-type-file-using-javascript

    promise = getFileData();
    promise.then(function (image) {
        $.ajax(
            {
                url: window.location.href,
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, "Authorization": "Token %s" },
                data: { "title": title, "description": desc, "markdown": markdown, "content": content, "image": image },
                success: function () {
                    alert("Successfully created post!");
                    location.reload();
                },
                error: function (response) { console.log(response); }

            }
        );
    })

}