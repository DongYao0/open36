// 题号 1–25 的 C++17 基准解；仅用于 HOJ 端到端压测的真实 AC 路径。
const SOLUTIONS = Object.freeze({
  '1': `#include <bits/stdc++.h>
using namespace std;int main(){char c;if(!(cin>>c))return 0;cout<<"  "<<c<<'\\n'<<" "<<c<<c<<c<<'\\n'<<c<<c<<c<<c<<c<<'\\n';}`,
  '2': `#include <bits/stdc++.h>
using namespace std;int main(){char c;cin>>c;cout<<char(c-'a'+'A');}`,
  '3': `#include <bits/stdc++.h>
using namespace std;int main(){double h,r;cin>>h>>r;cout<<(long long)ceil(20000.0/(3.14*r*r*h));}`,
  '4': `#include <bits/stdc++.h>
using namespace std;int main(){int a,b,c,d;cin>>a>>b>>c>>d;int t=c*60+d-a*60-b;cout<<t/60<<" "<<t%60;}`,
  '5': `#include <bits/stdc++.h>
using namespace std;int main(){double a,b,c;cin>>a>>b>>c;double p=(a+b+c)/2;cout<<fixed<<setprecision(1)<<sqrt(p*(p-a)*(p-b)*(p-c));}`,
  '6': `#include <bits/stdc++.h>
using namespace std;int main(){int a[3];for(int&i:a)cin>>i;sort(a,a+3);cout<<a[0]<<" "<<a[1]<<" "<<a[2];}`,
  '7': `#include <bits/stdc++.h>
using namespace std;int main(){long long a,b,c;cin>>a>>b>>c;if(a>b)swap(a,b);if(b>c)swap(b,c);if(a>b)swap(a,b);if(a+b<=c){cout<<"Not triangle";return 0;}long long x=a*a+b*b,y=c*c;if(x==y)cout<<"Right triangle\\n";else if(x>y)cout<<"Acute triangle\\n";else cout<<"Obtuse triangle\\n";if(a==b||b==c)cout<<"Isosceles triangle\\n";if(a==c)cout<<"Equilateral triangle";}`,
  '8': `#include <bits/stdc++.h>
using namespace std;int main(){long long n,a,b,ans=LLONG_MAX;cin>>n;for(int i=0;i<3;i++){cin>>a>>b;ans=min(ans,((n+a-1)/a)*b);}cout<<ans;}`,
  '9': `#include <bits/stdc++.h>
using namespace std;int main(){string s;cin>>s;int sum=0,k=1;for(char c:s)if(isdigit(c)&&k<=9)sum+=(c-'0')*k++;char v=sum%11==10?'X':char('0'+sum%11);if(s.back()==v)cout<<"Right";else{s.back()=v;cout<<s;}}`,
  '10': `#include <bits/stdc++.h>
using namespace std;int main(){int s,v;cin>>s>>v;int t=(8*60-(s+v-1)/v-10)%1440;if(t<0)t+=1440;cout<<setw(2)<<setfill('0')<<t/60<<":"<<setw(2)<<t%60;}`,
  '11': `#include <bits/stdc++.h>
using namespace std;int main(){long long a;int d=1;cin>>a;while(a>1){a/=2;d++;}cout<<d;}`,
  '12': `#include <bits/stdc++.h>
using namespace std;int main(){int n,x,ans=0;cin>>n>>x;for(int i=1;i<=n;i++)for(char c:to_string(i))ans+=c-'0'==x;cout<<ans;}`,
  '13': `#include <bits/stdc++.h>
using namespace std;int main(){string s;cin>>s;int x=0;for(char c:s)x+=c-'0';while(x>=10){int y=0;while(x)y+=x%10,x/=10;x=y;}cout<<x;}`,
  '14': `#include <bits/stdc++.h>
using namespace std;int main(){string s;getline(cin,s);if(!s.empty()&&s.back()=='!')s.pop_back();reverse(s.begin(),s.end());cout<<s;}`,
  '15': `#include <bits/stdc++.h>
using namespace std;int main(){long long n,x=1;cin>>n;for(long long p=2;p*p<=n;p++){int e=0;while(n%p==0)n/=p,e++;if(e&1)x*=p;}if(n>1)x*=n;cout<<x;}`,
  '16': `#include <bits/stdc++.h>
using namespace std;int main(){string s,o;cin>>s;for(int i=0;i<(int)s.size();){char c=s[i++];int k=1;if(i<(int)s.size()&&isdigit(s[i]))k=s[i++]-'0';o.append(k,c);}cout<<o;}`,
  '17': `#include <bits/stdc++.h>
using namespace std;bool prime(int n){if(n<2)return 0;for(int i=2;i*1LL*i<=n;i++)if(n%i==0)return 0;return 1;}int main(){int a,b;cin>>a>>b;for(int p:{5,7,11})if(p>=a&&p<=b)cout<<p<<'\\n';for(int i=10;i<=9999;i++){string s=to_string(i),t=s.substr(0,s.size()-1);reverse(t.begin(),t.end());int p=stoi(s+t);if(p>=a&&p<=b&&prime(p))cout<<p<<'\\n';}}`,
  '18': `#include <bits/stdc++.h>
using namespace std;long long g(long long a,long long b){return b?g(b,a%b):a;}int main(){int t;cin>>t;while(t--){long long a,b;cin>>a>>b;long long d=g(a,b);cout<<d<<" "<<a/d*b<<'\\n';}}`,
  '19': `#include <bits/stdc++.h>
using namespace std;int main(){double a,b,c;cin>>a>>b>>c;double m=max({a,b,c})/(max({a+b,b,c})*max({a,b,b+c}));cout<<fixed<<setprecision(3)<<m;}`,
  '20': `#include <bits/stdc++.h>
using namespace std;int main(){string s;cin>>s;int f[26]={};for(char c:s)f[c-'a']++;int p=0;for(int i=1;i<26;i++)if(f[i]>f[p])p=i;cout<<char('a'+p)<<" "<<f[p];}`,
  '21': `#include <bits/stdc++.h>
using namespace std;int main(){int n,x;vector<int>a;cin>>n;while(n--){cin>>x;if(x&1)a.push_back(x);}sort(a.begin(),a.end());for(int i=0;i<(int)a.size();i++){if(i)cout<<",";cout<<a[i];}}`,
  '22': `#include <bits/stdc++.h>
using namespace std;int main(){int n;double x;cin>>n>>x;double a=1,b=2*x;for(int i=2;i<=n;i++){double c=2*x*b-2*(i-1)*a;a=b;b=c;}cout<<fixed<<setprecision(2)<<(n==0?a:b);}`,
  '23': `#include <bits/stdc++.h>
using namespace std;int main(){string s;cin>>s;sort(s.begin(),s.end());cout<<s;}`,
  '24': `#include <bits/stdc++.h>
using namespace std;int main(){int t;cin>>t;while(t--){int n,k,a,coin=0,ans=0;cin>>n>>k;while(n--){cin>>a;if(a>=k)coin+=a;else if(a==0&&coin)coin--,ans++;}cout<<ans<<'\\n';}}`,
  '25': `#include <bits/stdc++.h>
using namespace std;int main(){int t,n;cin>>t;while(t--){cin>>n;vector<int>a;string s;while(n--){cin>>s;a.push_back(s.find('#')+1);}reverse(a.begin(),a.end());for(int i=0;i<(int)a.size();i++)cout<<(i?" ":"")<<a[i];cout<<'\\n';}}`,
});

export function solutionFor(problemId) { return SOLUTIONS[String(problemId)] || null; }

// 所有本批题目的标准输出均非空；该程序可编译、可运行，但必定得到 WA。
const WRONG_ANSWER = '#include <bits/stdc++.h>\nusing namespace std;int main(){cout<<-1<<"\\n";return 0;}';
export function wrongAnswerFor(problemId) {
  return SOLUTIONS[String(problemId)] ? WRONG_ANSWER : null;
}
