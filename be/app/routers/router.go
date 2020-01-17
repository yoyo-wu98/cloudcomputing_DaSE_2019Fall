package routers

import (
	"app/controllers"
	"github.com/astaxie/beego"
)

func init() {
    beego.Router("/", &controllers.MainController{})
    beego.Router("/send",&controllers.DataController{})
    beego.Router("/start",&controllers.CalController{})
    beego.Router("/cal",&controllers.ComputeController{})
    beego.Router("/test",&controllers.TestController{})
}
