/* Javascript for QuoteOfTheDayXBlock. */
function QuoteOfTheDayXBlock(runtime, element) {
	
	function URLshow(result) {
		//alert(result.unit_id)
		data=JSON.parse(result.unit_id)
		$('.concepts').append("List of concepts: <ul>")
		for(key in data){
			if(data[key].length!=0){
			$('.concepts').append("<li>Concept: "+key) 
			//var dir_links = data[key];
			//alert(typeof data[key])
			for(i=0;i<data[key].length;i++)
				$('.concepts').append("<a href='"+data[key][i]+"'>Link "+i+" </a>") 
			$('.concepts').append("</li>")
			}
			else {
			$('.concepts').append("<li>Local concept: "+key+"</li>")
			}
		}
		$('.concepts').append("</ul>")
		
		}
	
	var handlerUrl = runtime.handlerUrl(element, 'get_url');
	
	$(function ($) {
        /* Here's where you'd do things on page load. */
        var links = document.getElementsByTagName("button");
		for (var i = 0; i < links.length; i++) {
		        if (links[i].getAttribute("class")=="seq_other progress-0 nav-item active") {
		            link=links[i].getAttribute("data-id")
		        }
		}
        $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify({"URL": link}),
            success: URLshow
        });
    });
    }