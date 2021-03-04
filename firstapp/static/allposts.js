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

function viewPost(post_id) {
    window.location.replace(window.location.href+ "/" + post_id);
}

function makePost() {
    title = document.getElementById("title").value;
    desc = document.getElementById("desc").value;
    markdown = +document.getElementById("md").checked;
    content = document.getElementById("content").value;
    var image = 0;
    post_id = document.getElementById("post_id").value;

    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;



    // Cannot accept a non-numeric post id
    if(post_id.match(/[^0-9]/g)!=null) {
        alert("You have entered a non-numeric input, negative, or floating point number in the Post ID field. Please try again with a valid positive integer.");
        return;
    }

    // This code came from https://stackoverflow.com/questions/22680695/how-to-get-byte-array-from-input-type-file-using-javascript
    promise = getFileData();
    promise.then(function (image) {
        var method = 'POST'
        var URL = window.location.href;
        if(post_id != "") {
            method = 'PUT';
            URL = URL + "/" + post_id;

        }
        $.ajax(
            {
                url: URL,
                method: method,
                headers: { 'X-CSRFToken': csrftoken, "Authorization": "Token %s" },
                data: { "title": title, "description": desc, "markdown": markdown, "content": content, "image": image },
                success: function () {
                    alert("Successfully created post!");
                    location.reload();
                },
                error: function (response) {
                    if(response.status == 409) {alert("The post ID you entered has already been taken. Please enter another one.");}
                    else {console.log(response);}
                }

            }
        );
    })

}
