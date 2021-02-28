function makePost() {
    title = document.getElementById("title").value;
    desc = document.getElementById("desc").value;
    md = document.getElementById("md").checked;
    content = document.getElementById("content").value;
    image = document.getElementById("image").files;
    // Cannot accept empty values
    if(title == "" || desc == "" || content == "") {
        alert("Please fill out all of the fields.");
        return 1;
    }


    // This code came from https://stackoverflow.com/questions/22680695/how-to-get-byte-array-from-input-type-file-using-javascript

    var fileReader = new FileReader();
    var imageData = 0;
    if (fileReader && image && image.length) {
        fileReader.readAsArrayBuffer(image[0]);
        fileReader.onload = function () {
            imageData = fileReader.result;
        };
    }
    contenttype = "text/plain";
    if (md) {contenttype="text/markdown";}
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    /*
    $.ajax(
        {
            url:window.location.href,
            method:'POST',
            headers:{'X-CSRFToken':csrftoken, "Authorization":"Token %s"},
            data:{"title":title,"description":desc,"contenttype":contenttype,"content":content},
            success: function() {alert("Successfully created post!");},
            error: function(response) {console.log(response);}

        }
    );
    */
}