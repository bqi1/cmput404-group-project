// Get base64 encoded bytes from image field (async)
// This code came from https://stackoverflow.com/questions/22680695/how-to-get-byte-array-from-input-type-file-using-javascript
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
// If file field is filled out, set value of image link field to nothing
function resetLink() {
    imageUrl = document.getElementById("image_link");
    imageUrl.value = ""; 
}

// If image link field is filled out, set value of file field to nothing
function resetFile() {
    imageFile = document.getElementById("image_file");
    imageFile.value = "";
}

// When clicking the edit button, redirect the user to the specific post page
function viewPost(post_id) {
    window.location.replace(window.location.href + post_id);
}

function friendpostcomment(){
    window.location.replace(window.location.href + 'friendcommentpost/');
}

// Get parameters and send ajax POST / PUT request to post api view (to create post)

function makePost() {
    var username = "%s";
    var password = "%s";
    title = document.getElementById("title").value;
    desc = document.getElementById("desc").value;
    markdown = +document.getElementById("md").checked;
    content = document.getElementById("content").value;
    var image = 0;
    post_id = document.getElementById("post_id").value;

    privfriends = +document.getElementById("privfriends").checked;

    pa_list = document.getElementsByClassName("pa_id");
    priv_author = [];
    for(i=0;i<pa_list.length;i++) {priv_author.push(pa_list[i].value);}

    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;


    // Cannot accept a non-numeric post id
    if(post_id.match(/[^0-9]/g)!=null) {
        alert("You have entered a non-numeric input, negative, or floating point number in the Post ID field. Please try again with a valid positive integer.");
        return;
    }

    promise = getFileData();
    promise.then(function (image) {
        var method = 'POST'
        var URL = window.location.href;
        if(post_id != "") {
            method = 'PUT';
            URL = URL + post_id;

        }
        $.ajax(
            
            {
                url: URL,
                method: method,
                headers: { 'X-CSRFToken': csrftoken},
                beforeSend: function(xhr) { xhr.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password)); },                
                data: { "title": title, "description": desc, "markdown": markdown, "content": content, "image": image, "privfriends":privfriends,"priv_author":priv_author },
                success: function () {
                    alert("Successfully created post!");
                    location.reload();
                },
                error: function (response) {
                    if(response.status == 409) {alert("The post ID you entered has already been taken. Please enter another one.");}
                    else if(response.status == 404) {alert("One or more user ids entered into the author privacy field are not valid user ids.");}
                    else {console.log(response);}
                }

            }
        );
    })

}

// Add a new private author field when the + button is clicked
function addPrivateAuthor() {
    pa_list = document.getElementById("pa_list");
    private_author = document.createElement("li");
    br = document.createElement("br");

    private_author_id = document.createElement("input");
    private_author_id.setAttribute("class","pa_id")
    label = document.createElement("span");
    label.innerHTML = "Private Author Id";

    private_author.appendChild(label);
    private_author.appendChild(private_author_id);
    private_author.appendChild(br);

    pa_list.appendChild(private_author);
}

// Remove a new private author field when the - button is clicked
function removePrivateAuthor() {
    element_list = document.getElementById("pa_list");
    num_children = element_list.childNodes.length
    if (num_children>0){element_list.removeChild(element_list.childNodes[num_children-1]);}

}
