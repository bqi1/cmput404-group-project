var has_image = false;
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
// Read current post and put the current values into the input fields
function setDefaults() {
    // Set "back" url
    back = document.getElementById("back");
    back.setAttribute("href",window.location.href.match(/(.*)(?=\/)/g)[0]);

    title = document.getElementsByClassName("title")[0].innerHTML;
    desc = document.getElementsByClassName("desc")[0].innerHTML;
    markdown = +document.getElementsByClassName("md")[0].getAttribute("value");
    content = document.getElementsByClassName("content")[0].innerHTML;


    document.getElementById("title").setAttribute('value', title);
    document.getElementById("desc").setAttribute('value',desc);
    document.getElementById("md").checked = markdown;
    document.getElementById("content").value = content;

    image = document.getElementsByTagName("img");
    if(image.length >0) {has_image = true;}
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
// Get parameters and send ajax POST request to post api view (to edit post)
function editPost() {
    title = document.getElementById("title").value;
    desc = document.getElementById("desc").value;
    markdown = +document.getElementById("md").checked;
    content = document.getElementById("content").value;

    var image = 0;
    privfriends = +document.getElementById("privfriends").checked;


    ca_list = document.getElementsByClassName("ca_id");
    categories = [];
    for(i=0;i<ca_list.length;i++) {categories.push(ca_list[i].value);}

    pa_list = document.getElementsByClassName("pa_id");
    priv_author = [];
    for(i=0;i<pa_list.length;i++) {priv_author.push(pa_list[i].value);}

    unlisted = +document.getElementById("un").checked;


    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    promise = getFileData();
    promise.then(function (image) {
        modify = true;
        if(has_image == true && image == '0') {
            modify = confirm("You left the image field blank and the post currently has an image. Not selecting an image will remove the image. Are you sure you want to continue?");
        }

        if(modify == false) {return;}
        $.ajax(
            {
                url: window.location.href,
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, "Authorization": "Token %s" },
                data: { "title": title, "description": desc,"categories":categories, "markdown": markdown, "content": content, "image": image, "privfriends":privfriends, "priv_author":priv_author,"unlisted":unlisted },
                success: function () {
                    alert("Successfully modified post!");
                    window.location.replace(window.location.href.match(/(.*)(?=\/)/g)[0]);
                },
                error: function (response) {
                    if(response.status == 404) {alert("One or more usernames entered into the author privacy field are not valid usernames.");}

                    else {console.log(response);} }

            }
        );
    })
}

// Get parameters and send ajax DELETE request to post api view (to delete post)
function deletePost() {
    var username ="%s";
    var password = "%s";
    confirm_delete = confirm("Are you sure you want to delete this post?");
    if(confirm_delete == true) {
        csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        $.ajax(
            {
                url: window.location.href,
                method: 'DELETE',
                headers: { 'X-CSRFToken': csrftoken},
                beforeSend: function(xhr) { xhr.setRequestHeader("Authorization", "Basic " + btoa(username + ":" + password)); },                
                success: function () {
                    alert("Successfully deleted post!");
                    window.location.replace(window.location.href.match(/(.*)(?=\/)/g)[0]);
                },
                error: function (response) { console.log(response); }

            }
        );

    }

}


// Add a new category field when the + button is clicked
function addCategory() {
    pa_list = document.getElementById("ca_list");
    private_author = document.createElement("li");
    br = document.createElement("br");

    private_author_id = document.createElement("input");
    private_author_id.setAttribute("class","ca_id")
    label = document.createElement("span");
    label.innerHTML = "Category Tag";

    private_author.appendChild(label);
    private_author.appendChild(private_author_id);
    private_author.appendChild(br);

    pa_list.appendChild(private_author);
}

// Remove a new category field when the - button is clicked
function removeCategory() {
    element_list = document.getElementById("ca_list");
    num_children = element_list.childNodes.length
    if (num_children>0){element_list.removeChild(element_list.childNodes[num_children-1]);}

}


// Add a new private author field when the + button is clicked
function addPrivateAuthor() {
    pa_list = document.getElementById("pa_list");
    private_author = document.createElement("li");
    br = document.createElement("br");

    private_author_id = document.createElement("input");
    private_author_id.setAttribute("class","pa_id")
    label = document.createElement("span");
    label.innerHTML = "Private Author Username";

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