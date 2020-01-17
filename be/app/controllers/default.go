package controllers

import (
	"bufio"
	"github.com/astaxie/beego"
	_ "go/ast"
	_ "image/color"
	"log"
	"os"
	"os/exec"
	"strconv"
	"strings"
)
type MainController struct {
	beego.Controller
}

type DataController struct {
	beego.Controller
}

type CalController struct {
	beego.Controller
}

type ComputeController struct {
	beego.Controller
}


type TestController struct {
	beego.Controller
}


func (c *MainController) Get() {
	c.Data["Website"] = "beego.me"
	c.Data["Email"] = "astaxie@gmail.com"
	c.TplName = "index.tpl"
}


type Point struct {
	Latitude float64
	Longitude float64
}
var lastPoint Point;
var pointSlice []Point = make([]Point,10,20)

var PointPool []Point = make([]Point,1000,8000)
var now = 0
var startPlace = "1"
var endPlace = "1"

const threshold float64 = 0.000005

func calDistance(a,b Point) (float64){
	dis := (a.Longitude-b.Longitude)*(a.Longitude-b.Longitude) + (a.Latitude-b.Latitude)*(a.Latitude-b.Latitude)
	return dis
}
//得到距离最近的点以及其ID
func getNearstPoint(currentPoint Point) (p Point, num int){
	var mindis = 1000.0
	var token = 0
	for i := 0; i < len(PointPool); i++ {
		dis := calDistance(currentPoint,PointPool[i])
		if dis< threshold {
			return PointPool[i],i
		}
		if dis < mindis {
			mindis = dis
			token = i
		}
	}
	return PointPool[token],token
}


func tracefile(str_content string){
	fd,_:=os.OpenFile("./demo.txt",os.O_RDWR|os.O_CREATE|os.O_APPEND,0644)
	buf := []byte(str_content)
	fd.Write(buf)
	fd.Close()
}

type msg struct {
	Message string
}
func (this *TestController) Get()  {
	data := &msg{Message:"hello word"}
	this.Data["json"] = data
	this.ServeJSON()
}

/*获取一个点*/
func (this *DataController) Post() {

	longitude := this.GetString("longi")
	latitude := this.GetString("lati")

	res1,_ := strconv.ParseFloat(longitude,32)
	res2,_ := strconv.ParseFloat(latitude,32)

	var point Point
	point.Longitude = res1
	point.Latitude = res2
	pointSlice = append(pointSlice, point)
	p,the_num := getNearstPoint(point)
	//根据point 第三个参数
	endPlace = strconv.Itoa(the_num)
	strToWrite := strconv.FormatFloat(p.Latitude,'E',-1,32)+"\t"+strconv.FormatFloat(p.Longitude,'E',-1,32)+"\t"+startPlace+"\t"+endPlace
	startPlace = endPlace
	tracefile(strToWrite)
	data := &Point{p.Latitude,p.Longitude}
	lastPoint = *data
	this.Data["json"] = data
	this.ServeJSON()
}



/*加载数据库数据*/
func (this *CalController) Post() {

	file, err := os.Open("./35pages.txt")
	if err!=nil {
		log.Fatal(err)
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan()  {
		lineText := scanner.Text();
		a := strings.Split(lineText,",")
		lati,_ := strconv.ParseFloat(a[0],64)
		longi,_ := strconv.ParseFloat(a[1],64)
		s := Point{Latitude:lati,Longitude:longi}
		PointPool = append(PointPool, s)
	}
}



/*获得最后的结果*/
func (this * ComputeController) Post() {
	/*运行python脚本获得字符串式输出*/
	cmd := exec.Command("python","/Users/hjzhou/Gocode/newServer/src/app/controllers/a.py")
	out,err := cmd.CombinedOutput()
	if err!=nil {
		log.Println(err.Error())
	}
	p := strings.Replace(string(out),"\n","",100)
	a := strings.Split(p,"\t")
	min := 1000.0
	num :=-1
	for i := 0; i< len(a);i=i+2  {
		Lati, _ := strconv.ParseFloat(a[i],32)
		Longi,_ := strconv.ParseFloat(a[i+1],32)
		newPoint := Point{Latitude:Lati,Longitude:Longi}
		dis := calDistance(lastPoint,newPoint)
		if min<dis {
			min = dis
			num = i
		}
	}
	Lati,_ :=strconv.ParseFloat(a[num],32)
	Longi,_ := strconv.ParseFloat(a[num+1],32)

	//以json方式传递给前段
	data := &Point{Latitude:Lati,Longitude:Longi}
	this.Data["json"] = data
	this.ServeJSON()
}





