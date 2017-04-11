from django.http import HttpResponse  

def detect(request, cam):
  try:
      cam = int(cam)
  except ValueError:
      raise Http404()

  html='''
<meta http-equiv="Refresh" content="1">
<html>
 <body>
  <p><img src="/media/572.jpg" alt="detections"></p>
 </body>
</html>
  '''
  #html = str(cam)
#<script type="text/javascript">
#  setTimeout(function () { location.reload(true); }, 5000);
#</script>
  

  return HttpResponse(html)

