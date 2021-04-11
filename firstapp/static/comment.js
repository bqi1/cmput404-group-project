function commentPost(post_id){
    csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    $.ajax(
        {
            type:"POST",
            url:window.location.href + post_id + "/commentpost/",
            headers: { 'X-CSRFToken': csrftoken, "Authorization": "Token %s" },
            success: function () {
                alert("Successfully liked post!");
                location.reload();
            },
        }
    )
}

function viewComment(post_id){
    location.replace(window.location.href + post_id + "/comments/")
}
